function newPath() {
    $("#buttonFlow").attr("onclick", "");
    $("#buttonFlow").attr("onclick", "saveFlow()");
    $("#flowId").val("");
    $("#flowName").val("");
    $("#description").val("");
    $("#driverMemory").val('1g');
    $("#executorNumber").val('1');
    $("#executorMemory").val('1g');
    $("#executorCores").val('1');
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">create flow</span>',
        shadeClose: true,
        closeBtn: 1,
        shift: 7,
        area: ['580px', '520px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: $("#SubmitPage")
    });
}

function initDatatableFlowPage(testTableId, url, searchInputId) {
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
                        return responseHandlerFlow(data);
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
function responseHandlerFlow(res) {
    if (res) {
        var openHtmlStr = '<a class="btn" ' +
            'href="/piflow-web/page/flow/mxGraph/index.html?drawingBoardType=TASK&load=' + res.id + '"' +
            'target="_blank" ' +
            'style="margin-right: 2px;">' +
            '<i class="icon-share-alt icon-white"></i>' +
            '</a>';
        var editHtmlStr = '<a class="btn" ' +
            'href="javascript:void(0);" ' +
            'onclick="javascript:openFlowBaseInfo(' +
            '\'' + res.id + '\'' +
            ');" style="margin-right: 2px;">' +
            '<i class="icon-edit icon-white"></i>' +
            '</a>';
        var runHtmlStr = '<a class="btn" ' +
            'href="javascript:void(0);" ' +
            'onclick="javascript:runFlows(\'' + res.id + '\');" ' +
            'style="margin-right: 2px;">' +
            '<i class="icon-play icon-white"></i>' +
            '</a>';
        var debugHtmlStr = '<a class="btn" ' +
            'href="javascript:void(0);" ' +
            'onclick="javascript:runFlows(' +
            '\'' + res.id + '\',\'DEBUG\'' +
            ');" style="margin-right: 2px;">' +
            '<i class="fa-bug icon-white"></i>' +
            '</a>';
        var delHtmlStr = '<a class="btn" ' +
            'href="javascript:void(0);" ' +
            'onclick="javascript:deleteFlow(' +
            '\'' + res.id + '\',' +
            '\'' + res.name + '\'' +
            ');" style="margin-right: 2px;">' +
            '<i class="icon-trash icon-white"></i>' +
            '</a>';
        var templateHtmlStr = '<a class="btn" ' +
            'href="javascript:void(0);" ' +
            'onclick="javascript:saveTableTemplate(' +
            '\'' + res.id + '\',' +
            '\'' + res.name + '\'' +
            ');" style="margin-right: 2px;">' +
            '<i class="icon-check icon-white"></i>' +
            '</a>';
        return '<div style="width: 100%; text-align: center" >' + openHtmlStr + editHtmlStr + runHtmlStr + debugHtmlStr + delHtmlStr + templateHtmlStr + '</div>';
    }
    return "";
}

function openFlowBaseInfo(id) {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flow/queryFlowData",//This is the name of the file where I receive data in the background.
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
                var flowVo = dataMap.flow;
                $("#buttonFlow").attr("onclick", "");
                $("#buttonFlow").attr("onclick", "updateFlow()");
                $("#flowId").val(id);
                $("#flowName").val(flowVo.name);
                $("#description").val(flowVo.description);
                $("#driverMemory").val(flowVo.driverMemory);
                $("#executorNumber").val(flowVo.executorNumber);
                $("#executorMemory").val(flowVo.executorMemory);
                $("#executorCores").val(flowVo.executorCores);
                layer.open({
                    type: 1,
                    title: '<span style="color: #269252;">update flow</span>',
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

function saveFlow() {
    var flowName = $("#flowName").val();
    var description = $("#description").val();
    var driverMemory = $("#driverMemory").val();
    var executorNumber = $("#executorNumber").val();
    var executorMemory = $("#executorMemory").val();
    var executorCores = $("#executorCores").val();
    if (checkFlowInput(flowName, description, driverMemory, executorNumber, executorMemory, executorCores))
        ajaxRequest({
            cache: true,//Keep cached data
            type: "get",//Request type post
            url: "/flow/saveFlowInfo",//This is the name of the file where I receive data in the background.
            data: {
                name: flowName,
                description: description,
                driverMemory: driverMemory,
                executorNumber: executorNumber,
                executorMemory: executorMemory,
                executorCores: executorCores
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
                    layer.msg('create success ', {icon: 1, shade: 0, time: 2000}, function () {
                        var tempWindow = window.open('_blank');
                        if (tempWindow == null || typeof (tempWindow) == 'undefined') {
                            alert('The window cannot be opened. Please check your browser settings.')
                        } else {
                            tempWindow.location = "/piflow-web/mxGraph/drawingBoard?drawingBoardType=TASK&load=" + dataMap.flowId;
                        }
                    });
                } else {
                    layer.msg('creation failed', {icon: 2, shade: 0, time: 2000});
                }
            }
        });
}

function updateFlow() {
    var id = $("#flowId").val();
    var flowName = $("#flowName").val();
    var description = $("#description").val();
    var driverMemory = $("#driverMemory").val();
    var executorNumber = $("#executorNumber").val();
    var executorMemory = $("#executorMemory").val();
    var executorCores = $("#executorCores").val();
    if (checkFlowInput(flowName, description, driverMemory, executorNumber, executorMemory, executorCores))
        ajaxRequest({
            cache: true,//Keep cached data
            type: "POST",//Request type post
            url: "/flow/updateFlowBaseInfo",//This is the name of the file where I receive data in the background.
            data: {
                id: id,
                name: flowName,
                description: description,
                driverMemory: driverMemory,
                executorNumber: executorNumber,
                executorMemory: executorMemory,
                executorCores: executorCores
            },
            async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
            error: function (request) {//Operation after request failure
                layer.closeAll('page');
                layer.msg('update failed ', {icon: 2, shade: 0, time: 2000}, function () {
                    window.location.reload();
                });
                return;
            },
            success: function (data) {//Operation after request successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.closeAll('page');
                    layer.msg('update success', {icon: 1, shade: 0, time: 2000}, function () {
                        location.reload();
                    });
                } else {
                    layer.msg('update failed ', {icon: 2, shade: 0, time: 2000});
                }
            }
        });
}

//run
function runFlows(loadId, runMode) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    var data = {flowId: loadId}
    if (runMode) {
        data.runMode = runMode;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flow/runFlow",//This is the name of the file where I receive data in the background.
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
                    //Jump to monitoring page after successful startup
                    var tempWindow = window.open('_blank');
                    if (tempWindow == null || typeof (tempWindow) == 'undefined') {
                        alert('The window cannot be opened. Please check your browser settings.')
                    } else {
                        tempWindow.location = "/piflow-web/mxGraph/drawingBoard?drawingBoardType=PROCESS&processType=PROCESS&load=" + dataMap.processId;
                    }
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

function deleteFlow(id, name) {
    layer.confirm("Are you sure to delete '" + name + "' ?", {
        btn: ['confirm', 'cancel'] //Button
        , title: 'Confirmation prompt'
    }, function () {
        ajaxRequest({
            cache: true,//Keep cached data
            type: "get",//Request type post
            url: "/flow/deleteFlow",//This is the name of the file where I receive data in the background.
            data: {id: id},
            async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
            error: function (request) {//Operation after request failure
                return;
            },
            success: function (data) {//Operation after request successful
                if (data > 0) {
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

function checkFlowInput(flowName, description, driverMemory, executorNumber, executorMemory, executorCores) {
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
    if (driverMemory == '') {
        layer.msg('driverMemory Can not be empty', {icon: 2, shade: 0, time: 2000});
        document.getElementById('driverMemory').focus();
        return false;
    }
    if (executorNumber == '') {
        layer.msg('executorNumber Can not be empty', {icon: 2, shade: 0, time: 2000});
        document.getElementById('executorNumber').focus();
        return false;
    }
    if (executorMemory == '') {
        layer.msg('executorMemory Can not be empty', {icon: 2, shade: 0, time: 2000});
        document.getElementById('executorMemory').focus();
        return false;
    }
    if (executorCores == '') {
        layer.msg('executorCores Can not be empty', {icon: 2, shade: 0, time: 2000});
        document.getElementById('executorCores').focus();
        return false;
    }
    return true;
}

function saveTableTemplate(id, name) {
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
                templateType: "TASK"
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
