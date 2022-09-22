var newDatasourceWindow, openDatasourceId;

function initDataTablePage(testTableId, url, searchInputId) {
    var table = "";
    layui.use('table', function () {
        table = layui.table;

        //Method-level rendering
        table.render({
            elem: '#' + testTableId
            , url: (web_header_prefix + url)
            , headers: {
                Authorization: ("Bearer " + token)
            }
            , cols: [[
                {field: 'dataSourceName', title: 'Name', sort: true},
                {field: 'dataSourceDescription', title: 'Description', sort: true},
                {field: 'dataSourceType', title: 'DataSourceType', sort: true},
                // {
                //     field: 'right', title: 'Actions', sort: true, height: 100, templet: function (data) {
                //         return responseHandlerDataSource(data);
                //     }
                // }
            ]]
            , id: testTableId
            , page: true
        });
    });

    $("#" + searchInputId).bind('input propertychange', function () {
        searchMonitor(table, testTableId, searchInputId);
    });
}

// Replace the contents of the attribute
function updateSAttributes(updateHtmlStr, findType, attrName, oldContent, newContent) {
    var updateHtmlStr = $(updateHtmlStr);
    var idSelectObj = updateHtmlStr.find(findType);
    if (idSelectObj && idSelectObj.length > 0) {
        for (var i = 0; i < idSelectObj.length; i++) {
            var id_select_obj_i = idSelectObj[i];
            var id_select_obj_i_content = $(id_select_obj_i).attr(attrName);
            if (id_select_obj_i_content) {
                id_select_obj_i_content = id_select_obj_i_content.replace(new RegExp(oldContent, "gm"), newContent);
                $(id_select_obj_i).attr(attrName, id_select_obj_i_content);
            }
        }
    }
    return updateHtmlStr;
}

//Batch replacement
function replaceContent(sourceHtml, oldContent, newContent) {
    var splitArr = oldContent.split("R_R");
    var nameOldContent = splitArr.length === 2 ? splitArr[1] : splitArr[0];
    sourceHtml = updateSAttributes(sourceHtml, "div", "id", oldContent, "R_R" + newContent);
    sourceHtml = updateSAttributes(sourceHtml, "div a", "onclick", oldContent, "R_R" + newContent);
    sourceHtml = updateSAttributes(sourceHtml, "label input", "name", nameOldContent, newContent);
    sourceHtml = updateSAttributes(sourceHtml, "div input", "name", nameOldContent, newContent);
    return sourceHtml;
}

//Add a custom module
function addCustomProperty(copyId, targetId) {
    var sourceHtml = $("#" + copyId).clone();
    var targetObj = $("#" + targetId);
    var number = targetObj.children().length;
    var completedHtml = replaceContent(sourceHtml, "1Copy", number);
    $("#" + targetId).append(completedHtml.html());
}

//Delete custom module
function removeCustomModule(removeId, listId) {
    var listTotal = $("#" + listId).children().length;
    if (listTotal && listTotal > 1) {
        var number = removeId.split("R_R");
        if (number && number.length == 2) {
            $("#" + removeId).parent().remove();
            var forListTotal = listTotal;
            var currentNumber = number[1];
            while (currentNumber < forListTotal) {
                var nestNumber = currentNumber;
                var oldContentStr = "R_R" + (++nestNumber);
                var updateHtml = $("#" + number[0] + oldContentStr).parent();
                replaceContent(updateHtml, oldContentStr, currentNumber);
                currentNumber++;
            }
        } else {
            layer.msg("Incoming Id error please check！！");
        }
    } else {
        layer.msg("Please keep at least one！！");
    }
}

function dataSourceOpen(dataSourceId) {
    openDatasourceId = dataSourceId;
    newDatasourceWindow = layer.open({
        type: 2,
        title: '<span style="color: #269252;">data source</span>',
        shadeClose: true,
        closeBtn: 1,
        shift: 7,
        area: ['580px', '550px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: (web_drawingBoard + "/page/dataSource/dataSourceInput.html")
    });
    // ajaxRequest({
    //     cache: true,//Keep cached data
    //     type: "GET",//Request type post
    //     url: "/page/dataSource/getDataSourceInputPage.html",//This is the name of the file where I receive data in the background.
    //     //data:$('#loginForm').serialize(),//Serialize the form
    //     data: {"dataSourceId": dataSourceId},
    //     async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
    //     error: function (request) {//Operation after request failure
    //         layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
    //         return;
    //     },
    //     success: function (data) {//Operation after request successful
    //         newDatasourceWindow = layer.open({
    //             type: 1,
    //             title: '<span style="color: #269252;">data source</span>',
    //             shadeClose: true,
    //             closeBtn: 1,
    //             shift: 7,
    //             area: ['580px', '550px'], //Width height
    //             skin: 'layui-layer-rim', //Add borders
    //             content: data
    //         });
    //     }
    // });

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
function responseHandlerDataSource(res) {
    var dataAction = "";
    if (res) {
        var dataAction = '<a class="btn" '
            + 'href="javascript:void(0);" '
            + 'onclick="javascript:dataSourceOpen(\'' + res.id + '\');" '
            + 'style="margin-right: 2px;">'
            + '<i class="icon-edit icon-white"></i>'
            + '</a>'
            + '<a class="btn" '
            + 'href="javascript:void(0);" '
            + 'onclick="javascript:delDataSource(\'' + res.id + '\');" '
            + 'title="delete template"> '
            + '<i class="icon-trash icon-white"></i>'
            + '</a>';
    }
    return dataAction;
}

function changeDataSourceType(select) {
    $('#typeId').html("");
    $('#template_type_id').val("");
    $('#template_type_div_id').hide();
    if (select.value) {
        $('#typeContentId').show();
        if ('other' === select.value) {
            $('#customOtherDatasource').show();
            var datasourcePropertyHtml = $('#customKeyValueCopy').clone().html();
            var completedHtml = replaceContent(datasourcePropertyHtml, "1Copy", 0);
            $('#custom_property_list').html(completedHtml);
            $('#template_type_id').val("other");
            $("#layui-layer" + newDatasourceWindow).css("height", "520px");
        } else {
            $('#customOtherDatasource').hide();
            loadDataSourceById(select.value);
        }
    } else {
        $("#layui-layer" + newDatasourceWindow).css("height", "580px");
        $('#typeContentId').hide();
    }
}

function loadDataSourceById(dataSourceId) {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/datasource/getDatasourceById",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {"id": dataSourceId},
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var template = dataMap.data;
                var dataSourcePropertyVoList = template.dataSourcePropertyVoList;
                var datasourcePropertyHtml = '';
                if (dataSourcePropertyVoList && dataSourcePropertyVoList.length > 0) {
                    var dataSourcePropertyVoListLength = dataSourcePropertyVoList.length;
                    var newDatasourceWindow_jq_obj = $("#layui-layer" + newDatasourceWindow);
                    newDatasourceWindow_jq_obj.css("height", (dataSourcePropertyVoListLength * 43 + 427) + "px");
                    newDatasourceWindow_jq_obj.find(".layui-layer-content").css("height", (dataSourcePropertyVoListLength * 43 + 384) + "px");
                    for (var j = 0; j < dataSourcePropertyVoList.length; j++) {
                        var dataSourcePropertyVo = dataSourcePropertyVoList[j];
                        datasourcePropertyHtml += ('<div class="layui-form-item layui-form-text">'
                            + '<label class="layui-form-label">' + dataSourcePropertyVo.name + '</label>'
                            + '<input style="display:none;" '
                            + 'name="dataSourcePropertyVoList[' + j + '].name" '
                            + 'value="' + dataSourcePropertyVo.name + '" />'
                            + '<div class="layui-input-block">'
                            + '<input class="layui-input" autocomplete="off"'
                            + 'name="dataSourcePropertyVoList[' + j + '].value" '
                            + 'placeholder="please input name..." style="width: 95%;"/>'
                            + '</div>'
                            + '</div>');

                    }
                }
                $('#template_type_id').val(template.dataSourceType);
                $('#typeId').html(datasourcePropertyHtml);
            }

        }
    });
}

function saveOrUpdateDataSource(data) {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/datasource/saveOrUpdate",//This is the name of the file where I receive data in the background.
        data: data,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 1000}, function () {
                    window.location.reload();
                    //console.log(data);
                });
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 1000}, function () {
                });
            }
        }
    });
}

function delDataSource(datasourceId) {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/datasource/deleteDataSource",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {"dataSourceId": datasourceId},
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    window.location.reload();
                });
            }

        }
    });
}

function onloadPageData() {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/datasource/getDataSourceInputData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {"dataSourceId": openDatasourceId},
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            openDatasourceId = '';
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var dataSourceVoObj = dataMap.dataSourceVo;
                var templateListObj = dataMap.templateList;
                if (dataSourceVoObj) {
                    $("#selectTypeDivId").hide();
                    $("#submitBtnSpan").text('Update');
                    $("#updateDatasourceId").val(dataSourceVoObj.id);
                    $("#template_type_id").val(dataSourceVoObj.dataSourceType);
                    $("#dataSourceName").val(dataSourceVoObj.dataSourceName);
                    $("#dataSourceDescription").val(dataSourceVoObj.dataSourceDescription);
                    var dataSourcePropertyVoList = dataSourceVoObj.dataSourcePropertyVoList
                    if (dataSourcePropertyVoList) {
                        var typeId_element = $("#typeId");
                        typeId_element.html("");
                        dataSourcePropertyVoList.forEach((dataSourcePropertyVo, index) => {
                            var html = '<div class="layui-form-item layui-form-text">' +
                                '<label class="layui-form-label">' + dataSourcePropertyVo.name + '</label>' +
                                '<input style="display: none;"' +
                                'name="dataSourcePropertyVoList[' + index + '].id"' +
                                'value="' + dataSourcePropertyVo.id + '">' +
                                '<input style="display: none;"' +
                                'name="dataSourcePropertyVoList[' + index + '].name"' +
                                'value="' + dataSourcePropertyVo.name + '">' +
                                '<div class="layui-input-block">' +
                                '<input class="layui-input"' +
                                'autocomplete="off"' +
                                'placeholder="please input name..."' +
                                'style="width: 95%;"' +
                                'name="dataSourcePropertyVoList[' + index + '].value"' +
                                'value="' + dataSourcePropertyVo.value + '"/>' +
                                '</div>' +
                                '</div>';
                            typeId_element.append(html);
                        });
                    }
                    $('#typeContentId').show();
                } else {
                    $("#selectTypeDivId").show();
                    $("#submitBtnSpan").text('Create');
                    if (templateListObj) {
                        $('#type_select_id').html("");
                        $('#type_select_id').append('<option value="">please select type...</option>');
                        templateListObj.forEach((template, index) => {
                            var htmlOption = '<option value="' + template.id + '"' + '>' + template.dataSourceName + '</option>';
                            $('#type_select_id').append(htmlOption);
                        });
                        $('#type_select_id').append('<option value="other">Other</option>');
                    }
                    $('#typeContentId').hide();
                    //please select type...
                    $("#type_select_id").val($("#type_select_id option:contains(jdbc temolate)").val());
                    $("#type_select_id").change();
                    //other
                    $("#type_select_id").val("other");
                    $("#type_select_id").change();
                }
            } else {
                layer.msg("failed " + dataMap.errorMsg, {icon: 2, shade: 0, time: 1000}, function () {
                });
            }
        }
    });
}
