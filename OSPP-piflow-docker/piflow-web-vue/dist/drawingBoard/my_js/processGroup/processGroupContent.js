// var fullScreen = $('#fullScreen');
var processContent = $('#processContent');
var checkpointShow = $('#checkpointShow');
var isLoadProcessInfo = true;
var isEnd = false;
var timer;
var isProgress = false;

function processGroupOperationBtn(processState) {
    if ($('#runFlowGroup')) {
        if ("COMPLETED" !== processState && "FAILED" !== processState && "KILLED" !== processState) {
            $('#runFlowGroup').hide();
            $('#debugFlowGroup').hide();
            $('#stopFlowGroup').show();
            timer = window.setInterval("processGroupMonitoring(appId)", 5000);
        } else {
            $('#runFlowGroup').show();
            $('#debugFlowGroup').show();
            $('#stopFlowGroup').hide();
        }
        $("#groupProgress").text(load_obj_percentage + '%');
    }
}

function selectedFormation(pageId, e) {
    if (isLoadProcessInfo) {
        isLoadProcessInfo = false;
    }
    if (e && pageId) {
        var selectedRectShow = $('#selectedRectShow');
        if (selectedRectShow) {
            var imgStyleX = 0;
            var imgStyleY = 0;
            var imgStyleWidth = 66;
            var imgStyleHeight = 66;
            if (e) {
                var selectedStop = $(e).find('#stopImg' + pageId);
                imgStyleX = $(selectedStop).attr('x');
                imgStyleY = $(selectedStop).attr('y');
                imgStyleWidth = $(selectedStop).attr('width');
                imgStyleHeight = $(selectedStop).attr('height');
            }
            selectedRectShow.attr('x', imgStyleX).attr('y', imgStyleY).attr('width', imgStyleWidth).attr('height', imgStyleHeight);
        }
        queryProcessStop(processGroupId, pageId);
    } else {
        //alert("Necessary position parameters were not obtained");
        layer.msg("Necessary position parameters were not obtained", {icon: 2, shade: 0, time: 2000});
    }
}

function selectedPath(pageId, e) {
    if (isLoadProcessInfo) {
        isLoadProcessInfo = false;
    }
    if (pageId) {
        var selectedPathShow = $('#selectedPathShow');
        var selectedArrowShow = $('#selectedArrowShow');
        var pathStyleD = 'M 0 0 L 0 0';
        var arrowStyleD = 'M 0 0 L 0 0 L 0 0 L 0 0 Z';
        //var paths = $(e).find('path[name="arrowName"]');
        if (e) {
            pathStyleD = $(e).find('path[name="arrowName"]').attr("d");
            arrowStyleD = $(e).find('path[name="pathName"]').attr("d");
        }
        if (selectedPathShow) {
            selectedPathShow.attr('d', pathStyleD);
            selectedArrowShow.attr('d', arrowStyleD);
            selectedPathShow.show();
            selectedArrowShow.show();
            //selectedPolygonShow.attr('x', x).attr('y', y).attr('width', width).attr('height', height);
        }
        queryProcessGroupPath(processGroupId, pageId);
    } else {
        //alert("必要位置参数没有获得");
        layer.msg("Necessary position parameters were not obtained", {icon: 2, shade: 0, time: 2000});
    }
}

// Query basic information of process
function queryProcessGroup(processGroupId) {
    if (!isLoadProcessInfo) {
        isLoadProcessInfo = true;
    } else {
        if (!processGroupId || '' === processGroupId || 'null' === processGroupId || 'NULL' === processGroupId) {
            //alert("Id is empty, not obtained, please check!!");
            layer.msg("Id is empty, not obtained, please check!!", {icon: 2, shade: 0, time: 2000});
        } else {
            ajaxRequest({
                cache: true,//Keep cached data
                type: "POST",//Request type post
                url: "/processGroup/queryProcessGroup",//This is the name of the file where I receive data in the background.
                //data:$('#loginForm').serialize(),//Serialize the form
                data: {
                    processGroupId: processGroupId
                },
                async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
                error: function (request) {//Operation after request failure
                    console.log("fail");
                    return;
                },
                success: function (data) {//Operation after request successful
                    // console.log(data);
                    $('#processLeft').html(data)
                    $('#selectedRectShow').hide();
                    $('#selectedPathShow').hide();
                    $('#selectedArrowShow').hide();
                }
            });
        }
    }
    return;
}

//Query basic information about stops
function queryProcessStop(processGroupId, pageId) {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/processGroup/queryProcess",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processGroupId: processGroupId,
            pageId: pageId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            console.log("fail");
            return;
        },
        success: function (data) {//Operation after request successful
            // console.log(data);
            $('#processLeft').html(data);
            $('#selectedRectShow').show();
            $('#selectedArrowShow').hide();
            $('#selectedPathShow').hide();
            var stopsBundleShowText = $('#stopsBundleShow').text()
            if (stopsBundleShowText && stopsBundleShowText.toUpperCase() === "CN.PIFLOW.BUNDLE.HTTP.OPENURL") {
                var open_action = $('.open_action');
                if (open_action.length === 1) {
                    var open_action_i = $(open_action.get(0));
                    var a_href = open_action_i.text();
                    $(open_action.get(0)).after('&nbsp;&nbsp;&nbsp;&nbsp;<a class="btn btn-primary" href="' + a_href + '" style="color:#ffffff;" target="_blank">OPEN</a>');
                }
            }
        }
    });
}

//Query path basic information
function queryProcessGroupPath(processGroupId, pageId) {
    if (isLoadProcessInfo) {
        isLoadProcessInfo = false;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/processGroup/queryProcessPath",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processGroupId: processGroupId,
            pageId: pageId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            console.log("fail");
            return;
        },
        success: function (data) {//Operation after request successful
            // console.log(data);
            $('#processLeft').html(data);
            $('#selectedArrowShow').show();
            $('#selectedPathShow').show();
            $('#selectedRectShow').hide();
        }
    });
}

//Select run mode
function selectRunMode(runMode) {
    var runModeContent = '<div style="width: 100%;">'
        + '<div style="width: 210px;height: 50px;line-height: 50px;overflow: hidden;text-align: center;">'
        + '<button type="button" class="btn btn-default" onclick="runProcessGroup()">Run</button>&nbsp;'
        // + '<button type="button" class="btn btn-default" onclick="runProcessGroup(\'DEBUG\')">Debug</button>&nbsp;'
        + '<button type="button" class="btn btn-default" onclick="cancelRunProcessGroup()">Cancel</button>'
        + '</div>'
        + '</div>';
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">Select Run Mode</span>',
        shadeClose: true,
        closeBtn: 1,
        shift: 7,
        //area: ['600px', '200px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: runModeContent
    });

}

function cancelRunProcessGroup() {
    layer.closeAll();
    // fullScreen.hide();
    window.parent.postMessage(false);
    return;
}

//run
function getQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) return unescape(r[2]);
    return null;
}

function runProcessGroup(runMode) {
    // fullScreen.show();
    window.parent.postMessage(true);
    var id = getQueryString("load")
    var data = {
        id: id,
    }
    if (runMode) {
        data.runMode = runMode;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/processGroup/runProcessGroup",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: data,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            alert("Request Failed");
            // fullScreen.hide();
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//Operation after request successful
            //console.log("success");
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                // new_window_open("/page/processGroup/mxGraph/drawingBoard?drawingBoardType=PROCESS&processType=PROCESS_GROUP&load=" + dataMap.processGroupId);
                window_location_href("/page/processGroup/mxGraph/index.html?drawingBoard?drawingBoardType=PROCESS&processType=PROCESS_GROUP&load=" + dataMap.processGroupId);
            } else {
                alert("Startup Failed");
                // fullScreen.hide();
                window.parent.postMessage(false);
            }

        }
    });
}

//stop
function stopProcessGroup() {
    $('#stopFlowGroup').hide();
    // fullScreen.show();
    window.parent.postMessage(true);
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/processGroup/stopProcessGroup",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processGroupId: processGroupId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            alert("Request Failed");
            // fullScreen.hide();
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//Operation after request successful
            //console.log("success");
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                alert(dataMap.errorMsg);
                window.location.reload();
            } else {
                alert("Stop Failed:" + dataMap.errorMsg);
            }
            // fullScreen.hide();
            window.parent.postMessage(false);
        }
    });
}

function openLogWindow() {
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window width
    var open_window_width = (window_width > 300 ? window_width - 200 : window_width);
    var open_window_height = (window_height > 300 ? window_height - 150 : window_height);
    var logContent = '<div id="divPreId" style="height: ' + (open_window_height - 121) + 'px;width: 100%;">'
        + '<div id="preId" style="height: 100%; margin: 6px 6px 6px 6px;background-color: #f5f5f5;text-align: center;">'
        + '<span span style="font-size: 90px;margin-top: 15px;">loading....</span>'
        + '</div>'
        + '</div>';
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">Log Windows</span>',
        shadeClose: true,
        closeBtn: 1,
        shift: 7,
        area: [open_window_width + 'px', open_window_height + 'px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        btn: ['log', 'requestJson'], //button
        btn1: function (index, layero) {
            changeLogData("/processGroup/getGroupLogData", {"appId": appId});
            return false;
        },
        btn2: function (index, layero) {
            changeLogData("/processGroup/getStartGroupJson", {"processGroupId": loadId});
            return false;
        },
        content: logContent,
        success: function (layero) {
            layero.find('.layui-layer-btn').css('text-align', 'left');
            var bleBtn0 = layero.find('.layui-layer-btn0');
            var bleBtn1 = layero.find('.layui-layer-btn1');
            bleBtn0.removeClass('layui-layer-btn0');
            bleBtn1.removeClass('layui-layer-btn1');
            bleBtn0.addClass('layui-layer-btn1');
            bleBtn1.addClass('layui-layer-btn1');
        }
    });
    changeLogData("/processGroup/getGroupLogData", {"appId": appId});

}

function changeLogData(url, requestParam) {
    window.parent.postMessage(true);
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: url,//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: requestParam,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            window.parent.postMessage(false);
            var showLogHtmlWidth = $("#divPreId").width() - 20;
            var showLogHtml = ('<pre id="preId" style="height: 100%; width: ' + showLogHtmlWidth + 'px; margin: 0 auto;">');
            if (200 === dataMap.code) {
                showLogHtml += dataMap.data + '</pre>';
            } else {
                showLogHtml += 'Load Log Filed, ' + dataMap.errorMsg + '</pre>';
            }
            $("#divPreId").html(showLogHtml);
            $("#preId").scrollTop($("#preId")[0].scrollHeight);
            $(".layui-layer-content").scrollTop($(".layui-layer-content")[0].scrollHeight);
        }
    });
}

function processGroupMonitoring(appId) {
    if (appId === '') {
        return;
    }
    ajaxRequest({
        cache: true,
        type: "get",
        url: "/processGroup/getAppInfo",
        data: {appid: appId},
        async: true,
        traditional: true,
        error: function (request) {
            console.log("error");
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                if (dataMap.state && "" !== dataMap.state) {
                    if ('STARTED' !== dataMap.state && '100.00' === dataMap.progress) {
                        window.clearInterval(timer);
                        $('#runFlowGroup').show();
                        $('#debugFlowGroup').show();
                        $('#stopFlowGroup').hide();
                    }
                }
                var processGroupVo = dataMap.processGroupVo;
                if (processGroupVo && '' != processGroupVo) {
                    $("#groupProgress").html(dataMap.progress + "%");
                    //$("#groupProgress").css({'width': dataMap.progress + "%"});
                    if (!isProgress){
                        $("#processStartTimeShow").html(processGroupVo.startTime);
                        $("#processStopTimeShow").html(processGroupVo.endTime);
                        $("#processStateShow").html(dataMap.state);
                        $("#processProgressShow").html(dataMap.progress + "%");
                    }

                    // task
                    var processVoList = processGroupVo.processVoList;
                    if (processVoList && '' != processVoList) {
                        for (var i = 0; i < processVoList.length; i++) {
                            var processVo = processVoList[i];
                            if (processVo && '' != processVo) {
                                var sotpNameDB = processVo.name;
                                var sotpNameVal = $("#stopNameShow").text();
                                if (sotpNameDB === sotpNameVal) {
                                    $("#stopStartTimeShow").html(processVo.startTime);
                                    $("#stopStopTimeShow").html(processVo.endTime);
                                    $("#stopStateShow").html(processVo.state);
                                }
                                processGroupMonitor(processVo.pageId, processVo.state)
                            }
                        }
                    }
                    // group
                    var processGroupVoList = processGroupVo.processGroupVoList;
                    if (processGroupVoList && '' != processGroupVoList) {
                        for (var i = 0; i < processGroupVoList.length; i++) {
                            var processGroupVo = processGroupVoList[i];
                            if (processGroupVo && '' != processGroupVo) {
                                var sotpNameDB = processGroupVo.name;
                                var sotpNameVal = $("#stopNameShow").text();
                                if (sotpNameDB === sotpNameVal) {
                                    $("#processStartTimeShow").html(processGroupVo.startTime);
                                    $("#processStopTimeShow").html(processGroupVo.endTime);
                                    $("#processStateShow").html(processGroupVo.state);
                                    $("#processStateShow").html(processGroupVo.state);
                                    $("#processStateShow").html(processGroupVo.state);
                                    $("#processStateShow").html(processGroupVo.state);
                                }
                                processGroupMonitor(processGroupVo.pageId, processGroupVo.state)
                            }
                        }
                    }
                }
            }
        }
    });
}

function processGroupMonitor(pageId, processStopVoState) {
    var stopFailShow = $("#stopFailShow" + pageId);
    var stopOkShow = $("#stopOkShow" + pageId);
    var stopLoadingShow = $("#stopLoadingShow" + pageId);
    var stopImgChange = $("#stopImg" + pageId);
    if (processStopVoState) {
        if (processStopVoState.stringValue !== "INIT") {
            stopImgChange.attr('opacity', 1);
            if (processStopVoState && (processStopVoState.stringValue === "STARTED")) {
                stopFailShow.hide();
                stopOkShow.hide();
                stopLoadingShow.show();
            } else if (processStopVoState && processStopVoState.stringValue === "COMPLETED") {
                stopFailShow.hide();
                stopLoadingShow.hide();
                stopOkShow.show();
            } else if (processStopVoState && processStopVoState.stringValue === "FAILED") {
                stopOkShow.hide();
                stopLoadingShow.hide();
                stopFailShow.show();
            } else if (processStopVoState && processStopVoState.stringValue === "KILLED") {
                stopOkShow.hide();
                stopLoadingShow.hide();
                stopFailShow.show();
            }
        } else {
            stopImgChange.attr('opacity', 0.4);
        }
    } else {
        stopImgChange.attr('opacity', 0.4);
    }
}

function getDebugData(stopName, portName) {
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window width
    var jsonData = {"appId": appId, "stopName": stopName, "portName": portName};
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/page/process/getDebugDataHtml.html",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: jsonData,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            // var open_window_width = (window_width > 300 ? window_width - 200 : window_width) + "px";
            // var open_window_height = (window_height > 300 ? window_height - 200 : window_height) + "px";
            var open_window_width = (window_width > 300 ? 1200 : window_width);
            var open_window_height = (window_height > 400 ? 570 : window_height);
            layer.open({
                type: 1,
                title: '<span style="color: #269252;">Debug Data</span>',
                shadeClose: true,
                closeBtn: 1,
                shift: 7,
                area: [open_window_width, open_window_height], //Width height
                skin: 'layui-layer-rim', //Add borders
                content: data
            });
        }
    });
}

function loadDebugData() {
    var debug_app_id = $("#debug_app_id");
    var debug_stop_name = $("#debug_stop_name");
    var debug_port_name = $("#debug_port_name");
    var debug_data_last_read_line = $("#debug_data_last_read_line");
    var debug_data_last_file_name = $("#debug_data_last_file_name");

    if(!debug_data_last_read_line.html()){
        debug_data_last_read_line.html(0);
    }
    ajaxRequest({
        type: "POST",
        async: false,
        url: "/process/getDebugData", //Actual use, please change to the server real interface
        data: {
            "appId": debug_app_id.html(),
            "stopName": debug_stop_name.html(),
            "portName": debug_port_name.html(),
            "startFileName": debug_data_last_file_name.html(),
            "startLine": debug_data_last_read_line.html()
        },
        error: function () {
            layer.msg('An error occurred')
            return false;
        },
        success: function (rtnData) {
            var dataMap = JSON.parse(rtnData);
            if (200 === dataMap.code) {
                var div_table_list_obj = $('#div_table_list');
                var div_table_list_obj_children_length_add_1 = div_table_list_obj.children().length + 1;
                var debugData = dataMap.debugData;
                debug_data_last_read_line.html(debugData.lastReadLine);
                debug_data_last_file_name.html(debugData.lastFileName);
                isEnd = debugData.end;
                var schemaList = debugData.schema;
                var debugDataList = debugData.data;
                if (schemaList && schemaList.length > 0 && debugDataList && debugDataList.length > 0) {
                    var debug_data_table_id_obj = '<table id="debug_data_table_id_' + div_table_list_obj_children_length_add_1 + '" class="layui-table">';
                    var table_tr_th_all = '<thead><tr style="color: #1A7444;">';
                    for (var i = 0; i < schemaList.length; i++) {
                        table_tr_th_all += ('<th style="font-weight: bold;">' + schemaList[i] + '</th>');
                    }
                    table_tr_th_all += '</tr></thead>';
                    debug_data_table_id_obj += table_tr_th_all;
                    var table_tr_td_all = '';
                    for (var i = 0; i < debugDataList.length; i++) {
                        var debug_data_list_i_obj = JSON.parse(debugDataList[i]);
                        table_tr_td_all += '<tr>';
                        for (var j = 0; j < schemaList.length; j++) {
                            table_tr_td_all += ('<td>' + debug_data_list_i_obj[schemaList[j]] + '</td>');
                        }
                        table_tr_td_all += '</tr>';
                    }
                    debug_data_table_id_obj += (table_tr_td_all + '</table>');
                    div_table_list_obj.append(debug_data_table_id_obj);
                }
            }
        }
    });
}

function changePageNo(switchNo) {
    // Get all the tables under div_table_list and hide
    var div_table_list_obj = $('#div_table_list');
    var div_table_list_obj_children = div_table_list_obj.children();
    for (var i = 0; i < div_table_list_obj_children.length; i++) {
        $(div_table_list_obj_children[i]).hide();
    }
    //Find the table to switch
    var debug_data_table_id_current_obj = $("#debug_data_table_id_" + switchNo);
    // Determine whether there is content, there is content to display, otherwise request
    if (debug_data_table_id_current_obj.html()) {
        debug_data_table_id_current_obj.show();
    } else {
        loadDebugData();
    }
    // Retrieve all the tables under div_table_list
    div_table_list_obj = $('#div_table_list');

    // Find the element of the tag page for tag removal and replacement
    var current_page_obj = $('#current_page_id');
    // Whether the element of the tag page exists
    if (current_page_obj.html()) {
        var current_page_obj_em_arr = current_page_obj.find("em");
        for (var i = 0; i < current_page_obj_em_arr.length; i++) {
            var innerHTML_i = current_page_obj_em_arr[1].innerHTML;
            if (innerHTML_i) {
                current_page_obj.before('<a id="page_no_id_' + innerHTML_i + '" '
                    + 'href="javascript:changePageNo(' + innerHTML_i + ');">'
                    + innerHTML_i + '</a>');
                current_page_obj.remove();
                break;
            }
        }
    }
    if (switchNo == 1 && switchNo == div_table_list_obj.children().length && isEnd) {// Determine whether it is both the first page and the last page
        $("#debug_data_prev").attr("href", "javascript:void(0);");
        $("#debug_data_prev").addClass("layui-disabled");
        $("#debug_data_next").addClass("layui-disabled");
        $("#debug_data_next").attr("href", "javascript:void(0);");
    } else if (switchNo == 1) { // Determine if the page to be switched is the home page
        $("#debug_data_prev").attr("href", "javascript:void(0);");
        $("#debug_data_prev").addClass("layui-disabled");
        $("#debug_data_next").removeClass("layui-disabled");
        $("#debug_data_next").attr("href", "javascript:changePageNo(" + (switchNo + 1) + ");");
    } else if (switchNo == div_table_list_obj.children().length && isEnd) { // Determine if the page to be switched is the last page
        $("#debug_data_prev").removeClass("layui-disabled");
        $("#debug_data_prev").attr("href", "javascript:changePageNo(" + (switchNo - 1) + ");");
        $("#debug_data_next").addClass("layui-disabled");
        $("#debug_data_next").attr("href", "javascript:void(0);");
    } else {//When it is neither the first page nor the last page
        $("#debug_data_prev").removeClass("layui-disabled");
        $("#debug_data_prev").attr("href", "javascript:changePageNo(" + (switchNo - 1) + ");");
        $("#debug_data_next").removeClass("layui-disabled");
        $("#debug_data_next").attr("href", "javascript:changePageNo(" + (switchNo + 1) + ");");
    }
    var page_no_switch_obj = $('#page_no_id_' + switchNo);
    var current_page_no_obj = '<span id="current_page_id" class="layui-laypage-curr">'
        + '<em class="layui-laypage-em"></em>'
        + '<em>' + switchNo + '</em></span>';
    if (page_no_switch_obj.html()) {
        page_no_switch_obj.after(current_page_no_obj);
        page_no_switch_obj.remove();
    } else {
        $("#debug_data_next").before(current_page_no_obj);
    }
}