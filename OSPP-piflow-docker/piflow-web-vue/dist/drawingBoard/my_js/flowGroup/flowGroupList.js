function newFlowGroup() {
    $("#buttonFlowGroup").attr("onclick", "");
    $("#buttonFlowGroup").attr("onclick", "saveOrUpdateFlowGroup()");
    $("#flowGroupId").val("");
    $("#flowGroupName").val("");
    $("#description").val("");
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">create flow group</span>',
        shadeClose: true,
        closeBtn: 1,
        shift: 7,
        area: ['580px', '520px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: $("#SubmitPage")
    });
}

function initDatatableFlowGroupPage(testTableId, url, searchInputId) {
    var table = "";
    layui.use('table', function () {
        table = layui.table;

        //Method-level rendering
        table.render({
            elem: '#' + testTableId
            , headers: {
                Authorization: ("Bearer " + token)
            }
            , url: web_header_prefix + url
            , cols: [[
                {field: 'name', title: 'Name', sort: true},
                {field: 'description', title: 'Description', sort: true},
                {field: 'crtDttm', title: 'CreateTime', sort: true},
                {
                    field: 'right', title: 'Actions', sort: true, height: 100, templet: function (data) {
                        return responseActionsFlow(data);
                    }
                }
            ]]
            , id: testTableId
            , page: true
        });
    });

    $("#" + searchInputId).bind('input propertychange', function () {
        searchMonitor(table, testTableId, searchInputId);
    });
}

function searchMonitor(layui_table, layui_table_id, searchInputId) {
    //Perform overload
    layui_table.reload(layui_table_id, {
        page: {
            curr: 1 //Start again on page 1
        }
        , where: {param: $('#' + searchInputId).val()}
    }, 'data');
}

//Results returned in the background
function responseActionsFlow(res) {
    var actionsHtmlStr = '<div style="width: 100%; text-align: center" >' +
        '<a class="btn" ' +
        'href="javascript:void(0);"' +
        'onclick="javascript:openFlowGroup(\'' + res.id + '\'); "' +
        'style="margin-right: 2px;">' +
        '<i class="icon-share-alt icon-white"></i>' +
        '</a>' +
        '<a class="btn" ' +
        'href="javascript:void(0);"' +
        'onclick="javascript:openFlowBaseInfo(\'' + res.id + '\');" ' +
        'style="margin-right: 2px;">' +
        '<i class="icon-edit icon-white"></i>' +
        '</a>' +
        '<a class="btn" ' +
        'href="javascript:void(0);" ' +
        'onclick="javascript:listRunFlowGroup(\'' + res.id + '\');" ' +
        'style="margin-right: 2px;">' +
        '<i class="icon-play icon-white"></i>' +
        '</a>' +
        '<a class="btn" ' +
        'href="javascript:void(0);"' +
        'onclick="javascript:deleteFlowGroup(\'' + res.id + '\',\'' + res.name + '\');" ' +
        'style="margin-right: 2px;">' +
        '<i class="icon-trash icon-white"></i>' +
        '</a>' +
        '<a class="btn" ' +
        'href="javascript:void(0);"' +
        'onclick="javascript:listSaveFlowGroupTemplate(\'' + res.id + '\',\'' + res.name + '\');" ' +
        'style="margin-right: 2px;">' +
        '<i class="icon-check icon-white"></i>' +
        '</a>' +
        '</div>';
    return actionsHtmlStr;
}

function openFlowGroup(flowGroupId) {
    new_window_open('/page/flowGroup/mxGraph/index.html?drawingBoardType=GROUP&load=' + flowGroupId + '');
}

function openFlowBaseInfo(id) {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flowGroup/queryFlowGroupData",//This is the name of the file where I receive data in the background.
        data: {load: id},
        async: false,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.closeAll('page');
            layer.msg('request failed ', {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            layer.closeAll('page');
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var flowGroupVo = dataMap.flowGroupVo;
                $("#buttonFlowGroup").attr("onclick", "");
                $("#buttonFlowGroup").attr("onclick", "updateFlowGroup()");
                $("#flowGroupId").val(id);
                $("#flowGroupName").val(flowGroupVo.name);
                $("#description").val(flowGroupVo.description);
                layer.open({
                    type: 1,
                    title: '<span style="color: #269252;">update flow group</span>',
                    shadeClose: true,
                    closeBtn: false,
                    shift: 7,
                    closeBtn: 1,
                    area: ['580px', '520px'], //Width height
                    skin: 'layui-layer-rim', //Add borders
                    content: $("#SubmitPage")
                });
            } else {
                layer.msg('creation failed', {icon: 2, shade: 0, time: 2000});
            }
        }
    });
}

function saveOrUpdateFlowGroup() {
    var id = $("#flowGroupId").val();
    var flowGroupName = $("#flowGroupName").val();
    var description = $("#description").val();
    if (checkGroupInput(flowGroupName)) {
        ajaxRequest({
            cache: true,//Keep cached data
            type: "get",//Request type post
            url: "/flowGroup/saveOrUpdateFlowGroup",//This is the name of the file where I receive data in the background.
            data: {
                id: id,
                name: flowGroupName,
                description: description
            },
            async: false,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
            error: function (request) {//Operation after request failure
                layer.closeAll('page');
                layer.msg('creation failed ', {icon: 2, shade: 0, time: 2000});
                return;
            },
            success: function (data) {//Operation after request successful
                layer.closeAll('page');
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg('success ', {icon: 1, shade: 0, time: 2000}, function () {
                        new_window_open("/piflow-web/mxGraph/drawingBoard?drawingBoardType=GROUP&load=" + dataMap.flowGroupId);
                    });
                } else {
                    layer.msg('failed', {icon: 2, shade: 0, time: 2000});
                }
            }
        });
    }
}

function updateFlowGroup() {
    var id = $("#flowGroupId").val();
    var flowGroupName = $("#flowGroupName").val();
    var description = $("#description").val();
    if (checkGroupInput(flowGroupName)) {
        ajaxRequest({
            cache: true,//Keep cached data
            type: "get",//Request type post
            url: "/flowGroup/saveOrUpdateFlowGroup",//This is the name of the file where I receive data in the background.
            data: {
                id: id,
                name: flowGroupName,
                description: description
            },
            async: false,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
            error: function (request) {//Operation after request failure
                layer.closeAll('page');
                layer.msg('creation failed ', {icon: 2, shade: 0, time: 2000});
                return;
            },
            success: function (data) {//Operation after request successful
                layer.closeAll('page');
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg('success ', {icon: 1, shade: 0, time: 2000}, function () {
                        location.reload();
                    });
                } else {
                    layer.msg('failed', {icon: 2, shade: 0, time: 2000});
                }
            }
        });
    }
}

//run
function listRunFlowGroup(loadId, runMode) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    var data = {flowGroupId: loadId}
    if (runMode) {
        data.runMode = runMode;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flowGroup/runFlowGroup",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: data,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            //alert("Request Failed");
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000}, function () {
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            });

            return;
        },
        success: function (data) {//Operation after request successful
            //console.log("success");
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    new_window_open("/page/processGroup/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS_GROUP&load=" + dataMap.processGroupId);
                    // new_window_open("/processGroup/getProcessGroupById?parentAccessPath=grapheditor&processGroupId=" + dataMap.processGroupId);
                });
            } else {
                //alert("Startup failure：" + dataMap.errorMsg);
                layer.msg("Startup failure：" + dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                    location.reload();
                });
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

function deleteFlowGroup(id, name) {
    layer.confirm("Are you sure to delete '" + name + "' ?", {
        btn: ['confirm', 'cancel'] //button
        , title: 'Confirmation prompt'
    }, function () {
        ajaxRequest({
            cache: true,//Keep cached data
            type: "get",//Request type post
            url: "/flowGroup/deleteFlowGroup",//This is the name of the file where I receive data in the background.
            data: {id: id},
            async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
            error: function (request) {//Operation after request failure
                return;
            },
            success: function (data) {//Operation after request successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg('Delete Success', {icon: 1, shade: 0, time: 2000}, function () {
                        location.reload();
                    });
                } else {
                    layer.msg('Delete failed', {icon: 2, shade: 0, time: 2000});
                }
            }
        });
    }, function () {
    });
}

function checkGroupInput(flowName) {
    if (flowName == '') {
        layer.msg('flowName Can not be empty', {icon: 2, shade: 0, time: 2000});
        document.getElementById('flowName').focus();
        return false;
    }

    /*  if (description == '') {
         layer.msg('description不能为空！', {icon: 2, shade: 0, time: 2000});
         document.getElementById('description').focus();
         return false;
     } */
    return true;
}

function listSaveFlowGroupTemplate(id, name) {
    layer.prompt({
        title: 'please enter the template name',
        formType: 0,
        btn: ['submit', 'cancel']
    }, function (text, index) {
        layer.close(index);
        ajaxRequest({
            cache: true,//Keep cached data
            type: "get",//Request type post
            url: "/flowTemplate/saveFlowTemplate",//This is the name of the file where I receive data in the background.
            data: {
                load: id,
                name: text,
                templateType: "GROUP"
            },
            async: true,
            error: function (request) {//Operation after request failure
                console.log(" save template error");
                return;
            },
            success: function (data) {//Operation after request successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    });
                } else {
                    layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
                }
            }
        });
    });
}

