var isLoadProcessInfo = true;
var isEnd = false;

function initProcessContentPage(nodeArr) {
    $("#runFlow").attr("onclick", "getCheckpoint(" + getCheckpointParam + ")");
    $("#debugFlow").attr("onclick", "getCheckpoint(" + getCheckpointParam + ",'DEBUG')");
    $("#run_checkpoint_new").attr("onclick", "getCheckpoint(" + getCheckpointParam + ")");
    $("#debug_checkpoint_new").attr("onclick", "getCheckpoint(" + getCheckpointParam + ",'DEBUG')");
    if ($('#runFlow')) {
        if ("COMPLETED" !== processState && "FAILED" !== processState && "KILLED" !== processState) {
            $('#runFlow').hide();
            $('#debugFlow').hide();
            $('#stopFlow').show();
            timer = window.setInterval("processMonitoring(appId)", 5000);
        } else {
            $('#runFlow').show();
            $('#debugFlow').show();
            $('#stopFlow').hide();
        }
    }
    if (nodeArr && '' != nodeArr) {
        for (var i = 0; i < nodeArr.length; i++) {
            var processStopVoInit = nodeArr[i];
            monitor(processStopVoInit.pageId, processStopVoInit.state);
        }
    }
    // $("#progress").text(progress + "%");
    $("#progress").text(progress);
}

//  Get Checkpoint points
function getCheckpoint(pID, parentProcessId, processId, runMode) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/process/getCheckpointData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            pID: pID,
            parentProcessId: parentProcessId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            $('#runFlow').show();
            $('#debugFlow').show();
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var checkpointsSplitArray = dataMap.checkpointsSplit;
                if (checkpointsSplitArray) {
                    var layer_open_checkpoint_top = document.createElement("div");
                    var layer_open_checkpoint_btn_div = document.createElement("div");
                    layer_open_checkpoint_btn_div.setAttribute("style", "text-align: right;");

                    var layer_open_checkpoint_btn = document.createElement("div");
                    layer_open_checkpoint_btn.type = "button";
                    layer_open_checkpoint_btn.className = "btn btn-default";
                    layer_open_checkpoint_btn.setAttribute("style", "margin-right: 10px;");
                    if (runMode && 'DEBUG' === runMode) {
                        layer_open_checkpoint_btn.textContent = "Debug";
                        layer_open_checkpoint_btn.setAttribute('onclick', 'runProcess("' + processId + '","DEBUG")')
                    } else {
                        layer_open_checkpoint_btn.setAttribute('onclick', 'runProcess("' + processId + '")');
                        layer_open_checkpoint_btn.textContent = "Run"
                    }
                    layer_open_checkpoint_btn_div.appendChild(layer_open_checkpoint_btn);

                    var layer_open_checkpoint = document.createElement("div");
                    layer_open_checkpoint.id = "checkpointsContentDiv";
                    layer_open_checkpoint.style.height = "190px";
                    layer_open_checkpoint.style.overflow = "auto";
                    layer_open_checkpoint.style.margin = "10px";

                    for (var i = 0; i < checkpointsSplitArray.length; i++) {
                        var checkpoints_content_span = document.createElement("span");
                        checkpoints_content_span.style.display = "block";
                        checkpoints_content_span.style.margin = "5px 10px";
                        checkpoints_content_span.style.borderBottom = "1px dashed #ccc";
                        checkpoints_content_span.style.padding = "2px 0";
                        var checkpoints_content_span_input = document.createElement("input");
                        checkpoints_content_span_input.type = "checkbox";
                        checkpoints_content_span_input.value = checkpointsSplitArray[i];
                        checkpoints_content_span_input.style.marginRight = "5px";

                        var checkpoints_content_span_span = document.createElement("span");
                        checkpoints_content_span_span.textContent = checkpointsSplitArray[i];

                        var checkpoints_content_span_br = document.createElement("br");

                        checkpoints_content_span.appendChild(checkpoints_content_span_input);
                        checkpoints_content_span.appendChild(checkpoints_content_span_span);
                        checkpoints_content_span.appendChild(checkpoints_content_span_br);

                        layer_open_checkpoint.appendChild(checkpoints_content_span);

                    }

                    layer_open_checkpoint_top.appendChild(layer_open_checkpoint);
                    layer_open_checkpoint_top.appendChild(layer_open_checkpoint_btn_div);

                    openLayerWindowLoadHtml(layer_open_checkpoint_top.outerHTML, 500, 300, "Checkpoint", 0.3);
                    // $('#fullScreen').hide();
                    window.parent.postMessage(false);
                } else {
                    runProcess(processId, runMode);
                }
            }
        }
    });

}

function cancelRunProcess() {
    $('#checkpointShow').modal('hide');
    // $('#fullScreen').hide();
    window.parent.postMessage(true);
    return;
}

//run
function runProcess(processId, runMode) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    $('#runFlow').hide();
    $('#debugFlow').hide();
    var checkpointStr = '';
    $(".layui-layer-content").find("#checkpointsContentDiv").find("input[type='checkbox']:checked").each(function () {
        if ('' !== checkpointStr) {
            checkpointStr = (checkpointStr + ',');
        }
        checkpointStr = (checkpointStr + $(this).val());
    });
    var data = {
        id: processId,
        checkpointStr: checkpointStr
    };
    if (runMode) {
        data.runMode = runMode;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/process/runProcess",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: data,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            $('#runFlow').show();
            $('#debugFlow').show();
            //alert("Request Failed");
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//Operation after request successful
            //console.log("success");
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                //alert(dataMap.errorMsg);
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000});
                window_location_href("/page/process/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS&load=" + dataMap.processId);
            } else {
                //alert(dataMap.errorMsg);
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
                $('#runFlow').show();
                $('#debugFlow').show();
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            }

        }
    });
}

//stop
function stopProcess() {
    $('#stopFlow').hide();
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/process/stopProcess",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processId: processId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            stopFlow.show();
            //alert("Request Failed");
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//Operation after request successful
            //console.log("success");
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                //alert(dataMap.errorMsg);
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000});
                $('#runFlow').show();
                $('#debugFlow').show();
            } else {
                //alert("Stop Failed:" + dataMap.errorMsg);
                layer.msg("Stop Failed", {icon: 2, shade: 0, time: 2000});
                stopFlow.show();
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

function getLogUrl() {
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window width
    var open_window_width = (window_width > 300 ? window_width - 200 : window_width);
    var open_window_height = (window_height > 300 ? window_height - 150 : window_height);
    var logContent = '<div id="divPreId" style="height: ' + (open_window_height - 121) + 'px;width: 100%;">'
        + '<div id="preId" style="height: 100%; margin: 6px 6px 6px 6px;background-color: #f5f5f5;text-align: center;">'
        + '<span span style="font-size: 90px;margin-top: 15px;">loading....</span>'
        + '</div>'
        + '</div>';

    // + '<div style="margin-top: 5px;margin-bottom: 5px;margin-left: 10px;">'
    // + '<input type="button" class="btn btn-default" onclick="changeUrl(1)" value="stdout">'
    // + '<input type="button" class="btn btn-default" onclick="changeUrl(2)" value="stderr">'
    // + '</div>';

    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/process/getLogUrl",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {"appId": appId},
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            layer.open({
                type: 1,
                title: '<span style="color: #269252;">Log Windows</span>',
                shadeClose: true,
                closeBtn: 1,
                shift: 7,
                area: [open_window_width + 'px', open_window_height + 'px'], //Width height
                skin: 'layui-layer-rim', //Add borders
                btn: ['stdout', 'stderr'], //button
                btn1: function (index, layero) {
                    changeUrl(1);
                    return false;
                },
                btn2: function (index, layero) {
                    changeUrl(2);
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
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                stdoutLog = dataMap.stdoutLog;
                stderrLog = dataMap.stderrLog;
                changeUrl(1);
            }
        }
    });
}

function changeUrl(key) {
    var url
    switch (key) {
        case 1:
            url = stdoutLog;
            break;
        case 2:
            url = stderrLog;
            break;
        default:
            break;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/process/getLog",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {url: url},
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            return;
        },
        success: function (data) {//Operation after request successful
            console.log("success");
            if ('' !== data) {
                var content_td = $(data).find('.content')[0].innerHTML;
                var content_td_html = (('' !== content_td) ? content_td[0] : '');
                var showLogHtml = ('<div id="preId" style="height: 100%; margin: 6px 6px 6px 6px;background-color: #f5f5f5;">') + (content_td) + ('</div>');
                $("#divPreId").html(showLogHtml);
                $(".layui-layer-content").scrollTop($(".layui-layer-content")[0].scrollHeight);
            } else {
                $("#divPreId").html('<div id="preId" style="height: 100%; margin: 6px 6px 6px 6px;background-color: #f5f5f5;text-align: center;"><span style="font-size: 90px;margin-top: 15px;">Load Log Filed</span></div>');
            }
        }
    });
}

function processMonitoring(appId) {
    if (appId === '') {
        return;
    }
    ajaxRequest({
        cache: true,
        type: "get",
        url: "/process/getAppInfo",
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
                    if ("COMPLETED" === dataMap.state || "FAILED" === dataMap.state || "KILLED" === dataMap.state) {
                        window.clearInterval(timer);
                        $('#runFlow').show();
                        $('#debugFlow').show();
                        $('#stopFlow').hide();
                    }
                }
                var processVo = dataMap.processVo;
                if (processVo && '' != processVo) {
                    $("#progress").html(dataMap.progress + "%");
                    $("#processStartTimeShow").html(processVo.startTime);
                    $("#processStopTimeShow").html(processVo.endTime);
                    $("#processStateShow").html(dataMap.state);
                    $("#processProgressShow").html(dataMap.progress + "%");
                    // stop
                    var processStopVoList = processVo.processStopVoList;
                    if (processStopVoList && '' != processStopVoList) {
                        for (var i = 0; i < processStopVoList.length; i++) {
                            var processStopVo = processStopVoList[i];
                            if (processStopVo && '' != processStopVo) {
                                var sotpNameDB = processStopVo.name;
                                var sotpNameVal = $("#stopNameShow").text();
                                if (sotpNameDB === sotpNameVal) {
                                    $("#stopStartTimeShow").html(processStopVo.startTime);
                                    $("#stopStopTimeShow").html(processStopVo.endTime);
                                    $("#stopStateShow").html(processStopVo.state);
                                }
                                var pageId = processStopVo.pageId;
                                var processStopVoState = processStopVo.state;
                                monitor(pageId, processStopVoState)
                            }
                        }
                    }
                }
            }
        }
    });
}

function monitor(pageId, processStopVoState) {
    var stopFailShow = $("#stopFailShow" + pageId);
    var stopOkShow = $("#stopOkShow" + pageId);
    var stopLoadingShow = $("#stopLoadingShow" + pageId);
    var stopImgChange = $("#stopImg" + pageId);
    if (processStopVoState) {
        if (processStopVoState !== "INIT") {
            stopImgChange.attr('opacity', 1);
            if (processStopVoState && (processStopVoState === "STARTED")) {
                stopFailShow.hide();
                stopOkShow.hide();
                stopLoadingShow.show();
            } else if (processStopVoState && processStopVoState === "COMPLETED") {
                stopFailShow.hide();
                stopLoadingShow.hide();
                stopOkShow.show();
            } else if (processStopVoState && processStopVoState === "FAILED") {
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

    /*
    var stopPath = $('g[name="stopPageId' + pageId + '"]');
    if (stopPath.length > 0) {
        for (var i = 0; i < stopPath.length; i++) {
            var pathName = $(stopPath[i]).find('path[name="pathName"]');
            var arrowName = $(stopPath[i]).find('path[name="arrowName"]');
            if (processStopVoState && (processStopVoState === "STARTED")) {

            } else if (processStopVoState && processStopVoState === "COMPLETED") {
                $(pathName).attr('stroke', 'green');
                $(arrowName).attr('stroke', 'green').attr('fill', 'green');
            } else if (processStopVoState && processStopVoState === "FAILED") {
                $(pathName).attr('stroke', 'red');
                $(arrowName).attr('stroke', 'red').attr('fill', 'red');
            }
        }
    }
    */
}

function getDebugData(stopName, portName) {
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window width
    console.log(window_width,'------',window_height)
    var jsonData = {"appId": appId, "stopName": stopName, "portName": portName};
    ajaxLoad("", "/page/process/inc/debug_data_inc.html", function (data) {
        var open_window_width = (window_width > 300 ? 1200 : window_width);
        var open_window_height = (window_height > 400 ? 570 : window_height);
        openLayerWindowLoadHtml(data,open_window_width,open_window_height,"Debug Data");
        $("#debug_app_id").html(appId);
        $("#debug_stop_name").html(stopName);
        $("#debug_port_name").html(portName);
        changePageNo(1);
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
        url: '/process/getDebugData', //Actual use, please change to the server real interface
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