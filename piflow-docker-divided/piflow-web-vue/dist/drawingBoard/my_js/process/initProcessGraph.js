// Extends EditorUi to update I/O action states based on availability of backend
var graphGlobal = null;
var thisEditor = null;
// var fullScreen = $('#fullScreen');
var drawingBoardType = "PROCESS"
var index = true
var nodeArr, xmlDate, parentsId, processType, processGroupId, parentProcessId, pID, appId, processState,
    getCheckpointParam, progress;


function initProcessCrumbs(parentAccessPath) {
    if (parentAccessPath) {
        switch (parentAccessPath) {
            case "flow":
                $("#web_processList_navigation").hide();
                $("#web_flowList_navigation").show();
                $("#grapheditor_home_navigation").show();
                break;
            case "flowProcess":
                $("#web_processList_navigation").hide();
                $("#web_groupTypeProcessList_navigation").show();
                break;
            case "processGroupList":
                $("#web_processList_navigation").hide();
                $("#web_processGroupList_navigation").show();
                $("#web_getProcessGroupById_navigation").show();
                break;
        }
    }
}

function initProcessDrawingBoardData(loadId, parentAccessPath, backFunc) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        cache: true,//Keep cached data
        type: "get",//Request for get
        url: "/process/drawingBoardData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            loadId: loadId,
            parentAccessPath: parentAccessPath
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            // window.location.href = (web_baseUrl + "/error/404");
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                processId = dataMap.processId;
                processType = dataMap.processType;
                nodeArr = dataMap.nodeArr;
                xmlDate = dataMap.xmlDate;
                processGroupId = dataMap.processGroupId;
                parentsId = dataMap.processGroupId;
                appId = dataMap.appId;
                parentProcessId = dataMap.parentProcessId;
                pID = dataMap.pID;
                processState = dataMap.processState;
                progress = dataMap.percentage;
                getCheckpointParam = "'" + (dataMap.pID ? dataMap.pID : "") + "','" + (dataMap.parentProcessId ? dataMap.parentProcessId : "") + "', '" + (dataMap.processId ? dataMap.processId : "") + "'";
                top.document.getElementById('BreadcrumbProcess').style.display = 'block';
                top.document.getElementById('BreadcrumbProcessGroup').style.display = 'none';
                top.document.getElementById('BreadcrumbFlow').style.display = 'none';
                top.document.getElementById('BreadcrumbGroup').style.display = 'none';
                top.document.getElementById('BreadcrumbSchedule').style.display = 'none';
                var link = top.document.getElementById('ProcessParents');
                if (processGroupId !== 'null' && processGroupId !== undefined){
                    link.style.display = 'inline-block';
                    link.href='#/drawingBoard?src=/drawingBoard/page/processGroup/mxGraph/index.html?drawingBoardType=PROCESS&parentAccessPath=processGroupList&processType=PROCESS_GROUP&load='+processGroupId;
                }else {
                    link.style.display = 'none';
                }
            } else {
                //window.location.href = (web_baseUrl + "/error/404");
            }
            if (backFunc && $.isFunction(backFunc)) {
                backFunc(data);
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

function initProcessGraph() {
    Format.noEditing(true);
    $("#right-group-wrap")[0].style.display = "block";
    $("#precess-run")[0].style.display = "block";
    EditorUi.prototype.menubarHeight = 48;
    EditorUi.prototype.menubarShow = false;
    EditorUi.prototype.customToobar = true;

    var editorUiInit = EditorUi.prototype.init;
    EditorUi.prototype.init = function () {
        editorUiInit.apply(this, arguments);
        graphGlobal = this.editor.graph;
        thisEditor = this.editor;
        initMonitorIcon();
        this.actions.get('export').setEnabled(false);
        //Monitoring event
        graphGlobal.addListener(mxEvent.CLICK, function (sender, evt) {
            processMxEventClick(evt.properties.cell);
        });
        graphGlobal.addListener(mxEvent.SIZE, function (sender, evt) {
            changIconTranslate();
        });
        loadXml(xmlDate);
        graphGlobal.setCellsEditable(false);
        //graphGlobal.setCellsSelectable(false);
        graphGlobal.setConnectable(false);
        graphGlobal.setCellsMovable(false);
    };

    // Adds required resources (disables loading of fallback properties, this can only
    // be used if we know that all keys are defined in the language specific file)
    mxResources.loadDefaultBundle = false;
    var bundle = mxResources.getDefaultBundle(RESOURCE_BASE, mxLanguage) ||
        mxResources.getSpecialBundle(RESOURCE_BASE, mxLanguage);

    // Fixes possible asynchronous requests
    mxUtils.getAll([bundle, STYLE_PATH + '/default.xml'], function (xhr) {
        // Adds bundle text to resources
        mxResources.parse(xhr[0].getText());

        // Configures the default graph theme
        var themes = new Object();
        themes[Graph.prototype.defaultThemeName] = xhr[1].getDocumentElement();

        // Main
        new EditorUi(new Editor(urlParams['chrome'] == '0', themes));
    }, function () {
        document.body.innerHTML = '<center style="margin-top:10%;">Error loading resource files. Please check browser console.</center>';
    });
    ClickSlider();
}

//load xml file
function loadXml(loadStr, cells) {
    if (!loadStr) {
        return;
    }
    loadStr = replaceImageHead(loadStr, 'img');
    loadStr = replaceImageHead(loadStr, 'images');
    var xml = mxUtils.parseXml(loadStr);
    var node = xml.documentElement;
    var dec = new mxCodec(node.ownerDocument);
    dec.decode(node, graphGlobal.getModel());
    eraseRecord()
    if (cells) {
        var new_load_cells = graphGlobal.getModel().getCell(cells[0].id);
        graphGlobal.setSelectionCell(new_load_cells);
        flowMxEventClickFunc(new_load_cells, true);
    }
}

function replaceImageHead(str, end) {
    let loadDate = str;
    let regHead = '';
    switch (end) {
        case "img": {
            regHead = new RegExp(/style="image;html=1;labelBackgroundColor=#ffffff00;image=(\S*)\/img\//, "g");
            break;
        }
        case "images": {
            regHead = new RegExp(/style="image;html=1;labelBackgroundColor=#ffffff00;image=(\S*)\/images\//, "g");
            break;
        }
    }
    if (!regHead) {
        return "";
    }
    let reg_1 = loadDate.match(regHead);
    if (reg_1 && reg_1.length > 0) {
        let replaceArray = {};
        for (var i = 0; i < reg_1.length; i++) {
            let item = reg_1[i];
            let i_r = item.replace("style=\"image;html=1;labelBackgroundColor=#ffffff00;image=", "");
            if (replaceArray[i_r]) {
                continue;
            }
            replaceArray[i_r] = true;
        }
        for (var key in replaceArray) {
            if (key.indexOf("http") < 0) {
                key = "style=\"image;html=1;labelBackgroundColor=#ffffff00;image=" + key;
                let reg = new RegExp(key, "g")
                loadDate = loadDate.replace(reg, "style=\"image;html=1;labelBackgroundColor=#ffffff00;image=" + web_header_prefix + "/" + end + "/");
            } else {
                let reg = new RegExp(key, "g")
                loadDate = loadDate.replace(reg, web_header_prefix + "/" + end + "/");
            }
        }
    }
    return loadDate;
}

function processMxEventClick(cell) {
    $("#div_process_info_inc_load_id").hide();
    $("#div_process_path_inc_load_id").hide();
    $("#div_process_property_inc_load_id").hide();
    if (index) {
        $(".right-group").toggleClass("open-right");
        $(".ExpandSidebar").toggleClass("ExpandSidebar-open");
        $(".triggerSlider i").removeClass("fa fa-angle-left fa-2x ").toggleClass("fa fa-angle-right fa-2x");
        index = false
    }
    if (cell == undefined || cell && cell.style && (cell.style).indexOf("text\;") === 0) {
        //info
        queryProcessInfo(loadId);
    } else if (cell && cell.style && (cell.style).indexOf("image\;") === 0) {
        //stops
        queryProcessStopsProperty(loadId, cell.id);
    } else {
        //path
        queryProcessPathInfo(loadId, cell.id);
    }

}

function queryProcessInfo(processId) {
    $("#div_process_info_inc_load_id").show();
    $("#div_process_info_inc_id").show();
    $("#div_process_path_inc_id").hide();
    $("#div_process_property_inc_id").hide();
    ajaxRequest({
        cache: true,//Keep cached data
        type: "get",//Request for get
        url: "/process/queryProcessData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processId: processId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            $('#process_info_inc_loading').hide();
            $('#process_info_inc_load_fail').show();
            alert("Request Failed");
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            $('#process_info_inc_loading').hide();
            if (200 === dataMap.code) {
                // if (dataMap.processGroupId){
                //     processGroupId = dataMap.processGroupId;
                // }else {
                //     processGroupId = 'null';
                // }

                var processVo = dataMap.processVo;
                if (!processVo) {
                    $('#process_info_inc_no_data').show();
                } else {
                    //Process Basic Information
                    $("#span_processVo_id").text(processVo.id);
                    $("#span_processVo_name").text(processVo.name);
                    $("#span_processVo_description").text(processVo.description);
                    $("#span_processVo_crtDttmStr").text(processVo.crtDttmStr);
                    //Process Running Information
                    $("#processStartTimeShow").text(processVo.startTimeStr);
                    $("#processStopTimeShow").text(processVo.endTimeStr);
                    var processVo_state_text = (null !== processVo.state) ? processVo.state.stringValue : "INIT";
                    $("#processStateShow").text(processVo_state_text);
                    if (processVo.progress) {
                        $("#processProgressShow").text(processVo.progress + "%");
                    } else {
                        $("#processProgressShow").text("0.00%");
                    }


                    $('#process_info_inc_load_data').show();
                }
            } else {
                $('#process_info_inc_load_fail').show();
                //alert("Load Failed" + dataMap.errorMsg);
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

function queryProcessPathInfo(processId, pageId) {
    $("#div_process_path_inc_load_id").show();
    $("#div_process_info_inc_id").hide();
    $("#div_process_path_inc_id").show();
    $("#div_process_property_inc_id").hide();
    ajaxRequest({
        cache: true,//Keep cached data
        type: "get",//Request for get
        url: "/process/queryProcessPathData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processId: processId,
            pageId: pageId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            $('#process_path_inc_loading').hide();
            $('#process_path_inc_load_fail').show();
            alert("Request Failed");
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            $('#process_path_inc_loading').hide();
            if (200 === dataMap.code) {
                var processPathVo = dataMap.processPathVo;
                if (!processPathVo) {
                    $('#process_path_inc_no_data').show();
                } else {
                    // Process Path Information
                    $("#span_processPathVo_from").text(processPathVo.from);
                    $("#span_processPathVo_outport").text(processPathVo.outport);
                    $("#span_processPathVo_inport").text(processPathVo.inport);
                    $("#span_processPathVo_to").text(processPathVo.to);

                    if (dataMap.runModeType && dataMap.runModeType.text === 'DEBUG') {
                        $("#div_view_flow_data").html('<input type="button" class="btn btn-primary" onclick="getDebugData(\'' + processPathVo.from + '\',\'' + processPathVo.outport + '\')" value="View Flow Data">');
                        $("#div_view_flow_data").show();
                    }

                    $('#process_path_inc_load_data').show();
                }
            } else {
                $('#process_path_inc_load_fail').show();
                //alert("Load Failed" + dataMap.errorMsg);
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

function queryProcessStopsProperty(processId, pageId) {
    $("#div_process_property_inc_load_id").show();
    $("#div_process_info_inc_id").hide();
    $("#div_process_path_inc_id").hide();
    $("#div_process_property_inc_id").show();
    ajaxRequest({
        cache: true,//Keep cached data
        type: "get",//Request for get
        url: "/process/queryProcessStopData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            processId: processId,
            pageId: pageId
        },
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            $('#process_property_inc_loading').hide();
            $('#process_property_inc_load_fail').show();
            alert("Request Failed");
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            $('#process_property_inc_loading').hide();
            $("#div_processStopVo_processStopPropertyVo").html("");
            if (200 === dataMap.code) {
                var processStopVo = dataMap.processStopVo;
                if (!processStopVo) {
                    $('#process_property_inc_no_data').show();
                } else {

                    // Stop Basic Information
                    $("#stopNameShow").text(processStopVo.name);
                    $("#span_processStopVo_description").text(processStopVo.description);
                    $("#span_processStopVo_groups").text(processStopVo.groups);
                    $("#stopsBundleShow").text(processStopVo.bundel);
                    $("#span_processStopVo_owner").text(processStopVo.owner);
                    if ( processStopVo.visualizationType === '' ){
                        $("#process_info_inc_load_chart").css('display','none');
                    }else {
                        $("#process_info_inc_load_chart").css('display','block');
                        $("#process_info_inc_load_getChartBtn").attr('data', processStopVo.visualizationType);
                        $("#process_info_inc_load_getChartBtn").attr('name', processStopVo.name);
                    }


                    //Stop Property Information
                    var processStopPropertyVoList = processStopVo.processStopPropertyVoList;
                    if (processStopPropertyVoList) {
                        var processStopPropertyVoListHtml = '<span>';
                        processStopPropertyVoList.forEach(item => {
                            if (item) {
                                var processStopPropertyVo = '<span>' + item.displayName + ':</span><span class="open_action">' + item.customValue + '</span><br>';
                                processStopPropertyVoListHtml += processStopPropertyVo;
                            }
                        });
                        processStopPropertyVoListHtml += '</span>';
                        $("#div_processStopVo_processStopPropertyVo").append(processStopPropertyVoListHtml);
                        $("#div_processStopVo_processStopPropertyVoList").show();
                    }
                    //Stop Running Information
                    $("#stopStartTimeShow").text(processStopVo.startTimeStr);
                    $("#stopStopTimeShow").text(processStopVo.endTimeStr);
                    var processStopVo_state_text = (null !== processStopVo.state) ? processStopVo.state : "INIT";
                    $("#stopStateShow").text(processStopVo_state_text);

                    $('#process_property_inc_load_data').show();
                }
            } else {
                $('#process_property_inc_load_fail').show();
                //alert("Load Failed" + dataMap.errorMsg);
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

//Erase drawing board records
function eraseRecord() {
    thisEditor.lastSnapshot = new Date().getTime();
    thisEditor.undoManager.clear();
    thisEditor.ignoredChanges = 0;
    thisEditor.setModified(false);
}

function initMonitorIcon() {

    setTimeout(() => {
        console.log("svg_element")
        var svg_element = document.getElementsByClassName('geDiagramBackdrop geDiagramContainer')[0].getElementsByTagName("svg")[0];
        nodeArr.forEach(item => {
            var img_element_init = document.createElementNS("http://www.w3.org/2000/svg", "image");
            img_element_init.setAttribute("x", 0);
            img_element_init.setAttribute("y", 0);
            img_element_init.setAttribute("width", 20);
            img_element_init.setAttribute("height", 20);
            img_element_init.setAttribute("PiFlow_IMG", "IMG");
            img_element_init.href.baseVal = web_drawingBoard + "/img/Loading.gif";
            img_element_init.setAttribute("id", "stopLoadingShow" + item.pageId);

            var img_element_ok = document.createElementNS("http://www.w3.org/2000/svg", "image");
            img_element_ok.setAttribute("x", 0);
            img_element_ok.setAttribute("y", 0);
            img_element_ok.setAttribute("width", 20);
            img_element_ok.setAttribute("height", 20);
            img_element_ok.setAttribute("PiFlow_IMG", "IMG");
            img_element_ok.href.baseVal = web_drawingBoard + "/img/Ok.png";
            img_element_ok.setAttribute("id", "stopOkShow" + item.pageId);

            var img_element_fail = document.createElementNS("http://www.w3.org/2000/svg", "image");
            img_element_fail.setAttribute("x", 0);
            img_element_fail.setAttribute("y", 0);
            img_element_fail.setAttribute("width", 20);
            img_element_fail.setAttribute("height", 20);
            img_element_fail.setAttribute("PiFlow_IMG", "IMG");
            img_element_fail.href.baseVal = web_drawingBoard + "/img/Fail.png";
            img_element_fail.setAttribute("id", "stopFailShow" + item.pageId);
            img_element_init.style.display = "none";
            img_element_fail.style.display = "none";
            img_element_ok.style.display = "none";
            if (item.state) {
                if (item.state !== "INIT") {
                    //stopImgChange.attr('opacity', 1);
                    if (item.state && (item.state === "STARTED")) {
                        img_element_init.style.display = "block";
                        img_element_fail.style.display = "none";
                        img_element_ok.style.display = "none";
                    } else if (item.state && item.state === "COMPLETED") {
                        img_element_init.style.display = "none";
                        img_element_fail.style.display = "none";
                        img_element_ok.style.display = "block";
                    } else if (item.state && item.state === "FAILED") {
                        img_element_init.style.display = "none";
                        img_element_fail.style.display = "block";
                        img_element_ok.style.display = "none";
                    } else if (item.state && item.state === "KILLED") {
                        img_element_init.style.display = "none";
                        img_element_fail.style.display = "block";
                        img_element_ok.style.display = "none";
                    }
                }
            }

            if (svg_element && img_element_init && img_element_ok && img_element_fail) {
                var g_element = document.createElementNS("http://www.w3.org/2000/svg", "g");
                g_element.appendChild(img_element_init);
                g_element.appendChild(img_element_ok);
                g_element.appendChild(img_element_fail);
                svg_element.append(g_element);
            }
        });
        changIconTranslate();
    }, 300)
}

function changIconTranslate() {
    var iconPositionElementArr = document.querySelectorAll("div[style='display: inline-block; font-size: 1px; font-family: PiFlow; color: #FFFFFF; line-height: 1.2; pointer-events: all; white-space: nowrap; ']");
    if (iconPositionElementArr && iconPositionElementArr.length > 0) {
        var iconPositionArr = {};
        iconPositionElementArr.forEach(item => {
            var x_y_div = item.parentElement.parentElement.style;
            var x_Position = x_y_div['margin-left'].replace("px", "");
            var y_Position = x_y_div['padding-top'].replace("px", "");
            iconPositionArr['stopLoadingShow' + item.textContent] = {x: x_Position, y: y_Position};
            iconPositionArr['stopFailShow' + item.textContent] = {x: x_Position, y: y_Position};
            iconPositionArr['stopOkShow' + item.textContent] = {x: x_Position, y: y_Position};
        });
        var imgsArr = document.querySelectorAll("image[PiFlow_IMG='IMG']");
        imgsArr.forEach(item => {
            var iconPosition = iconPositionArr[item.id]
            if (iconPosition) {
                item.setAttribute("transform", "translate(" + iconPosition.x + "," + iconPosition.y + ")");
            }
        });
    }
}

window.onresize = function (e) {
    setTimeout(() => {
        changIconTranslate()
    }, 300);
}

function ClickSlider() {
    $(".triggerSlider").click(function () {
        var flag = ($(".triggerSlider i:first").hasClass("fa fa-angle-right fa-2x"));
        if (flag === false)
            $(".triggerSlider i").removeClass("fa fa-angle-left fa-2x ").toggleClass("fa fa-angle-right fa-2x");
        else
            $(".triggerSlider i").removeClass("fa fa-angle-right fa-2x").toggleClass("fa fa-angle-left fa-2x");

        $(".right-group").toggleClass("open-right");
        $(".ExpandSidebar").toggleClass("ExpandSidebar-open");
        $(this).toggleClass("triggerSlider-open");
        index = !index
    });
}

function getChart(e,softData,isSoft, ifTheFirst) {
    $("#process_info_inc_load_getChartBtn").attr('disabled',true);
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window width
    var open_window_width = (window_width > 300 ? window_width - 200 : window_width);
    var open_window_height = (window_height > 300 ? window_height - 150 : window_height);
    var logContent = '<div id="divPreId" style="height: 100%;width: 100%;">'
        + '<div id="preId" style="height: 100%;width: 100%; background-color: #f5f5f5;text-align: center;">'
        + '<div id="chartLine" style="width: 100%;height:90%;margin:0 auto; display: none"></div>'
        + '<div id="chartScatter" style="width: 100%;height:90%;margin:0 auto; display: none"></div>'
        + '<div id="chartBar" style="width: 100%;height:90%;margin:0 auto; display: none"></div>'
        + '<div id="chartPie" style="width: 100%;height:90%;margin:0 auto; display: none"></div>'
        // + '<div id="chartTable" style="width: 100%;height:90%;margin:0 auto; display: none;padding: 20px 20px 0 20px;">' +
        // '<table class="table table-striped table-bordered" id="statisticsTableMode" cellspacing="0" style="width: 100%"></table></div>'
        + '</div>'
        + '</div>';
    var parameter= {},type='', name='', ifFirst = true;
    if (softData){
        parameter = softData;
        type = softData.visualizationType;
        name = softData.stopName;
        ifFirst = ifTheFirst;
        if (parameter.isSoft){
            parameter.isSoft = false;
        }else
            parameter.isSoft = true;
    }else {
        type = e.getAttribute('data');
        name = e.getAttribute('name');
        parameter = {
            appId: appId,
            stopName: name,
            visualizationType: type,
            isSoft: true,
        }
    }
    // 可视化图表数据

    ajaxRequest({
        cache: true,//Keep cached data
        type: "get",//Request type post
        url: "/process/getVisualizationData",//This is the name of the file where I receive data in the background.
        //data:$('#loginForm').serialize(),//Serialize the form
        data: parameter,
        async: true,//Setting it to true indicates that other code can still be executed after the request has started. If this option is set to false, it means that all requests are no longer asynchronous, which also causes the browser to be locked.
        error: function (request) {//Operation after request failure
            $("#process_info_inc_load_getChartBtn").attr('disabled',false);
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {//Operation after request successful
            $("#process_info_inc_load_getChartBtn").attr('disabled',false);
            var dataMap = JSON.parse(data), visualizationData = {};
            visualizationData = JSON.parse(dataMap.visualizationData);
            if (type === 'TABLE'){
                // 判断页面是否加载完毕
                if(document.readyState === 'complete') {
                    window.parent['visualizationTable']({value: visualizationData.data});
                }
            }else {
                if (ifFirst){
                    layer.open({
                        type: 1,
                        title: '<span style="color: #269252;">View Charts</span>',
                        shadeClose: true,
                        closeBtn: 1,
                        shift: 7,
                        area: [open_window_width + 'px', open_window_height + 'px'], //Width height
                        skin: 'layui-layer-rim', //Add borders
                        // btn: ['stdout', 'stderr'], //button
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
                            switch (type){
                                case 'PIECHART':
                                    // 饼状图
                                    $('#chartPie').css('display','block');
                                    var newArr = [];
                                    for(var i=0;i<visualizationData.legend.length;i++){
                                        newArr.push(Number(visualizationData.legend[i]))
                                    }
                                    var chartPie = echarts.init(document.getElementById('chartPie'));
                                    var PieOption = {
                                        color: ['#726a95', '#709fb0', '#a0c1b8', '#f4ebc1', '#e4e4e4', '#ad6989', '#f9d89c', '#7fdbda', '#ba7967', '#e2979c', '#abc2e8'],
                                        // title: {
                                        //     text: '',
                                        //     subtext: '',
                                        //     left: 'center'
                                        // },
                                        tooltip: {
                                            trigger: 'item',
                                            formatter: '{a} <br/>{b} : {c} ({d}%)'
                                        },
                                        legend: {
                                            // orient: 'vertical',
                                            top: 10,
                                            left: 'center',
                                            data: newArr
                                        },
                                        toolbox: {
                                            right: '50',
                                            feature: {
                                                saveAsImage: {}
                                            }
                                        },
                                        series: [
                                            {
                                                name: '访问来源',
                                                type: 'pie',
                                                radius: '55%',
                                                center: ['50%', '60%'],
                                                selectedMode: 'single',
                                                data: visualizationData.series,
                                                emphasis: {
                                                    itemStyle: {
                                                        shadowBlur: 10,
                                                        shadowOffsetX: 0,
                                                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                                                    }
                                                }
                                            }
                                        ]
                                    };
                                    chartPie.setOption(PieOption,true);
                                    break;
                                case 'LINECHART':
                                    $('#chartLine').css('display','block');
                                    for (var i=0;i<visualizationData.series.length;i++){
                                        // visualizationData.series[i].areaStyle = {};
                                        visualizationData.series[i].smooth = true;
                                        for (var key in visualizationData.series[i]){
                                            if (key === 'stack'){
                                                visualizationData.series[i][key] = 'count';
                                            }
                                        }
                                    }
                                    // visualizationData.xAxis.data = visualizationData.xAxis.data.map(i => parseInt(i, 0));
                                    // 折线图
                                    var myChart = echarts.init(document.getElementById('chartLine'));
                                    var option = {
                                        title: {
                                            text: ''
                                        },
                                        color: ['#879DDA', '#9FE080', '#FDD963', '#F86C6C', '#ad6989', '#40B27D', '#FE9059', '#A76AC3'],
                                        tooltip: {
                                            trigger: 'axis',
                                            axisPointer: {
                                                type: 'cross',
                                                label: {
                                                    backgroundColor: '#6a7985'
                                                }
                                            }
                                        },
                                        legend: {
                                            data: visualizationData.legend
                                        },
                                        toolbox: {
                                            right: '50',
                                            feature: {
                                                show: false,

                                                saveAsImage: {},
                                                myTool1: {    //必须要my开头
                                                    show: true,
                                                    title: '排序',
                                                    iconStyle: {
                                                        borderColor: '#9f9f9f'
                                                    },
                                                    icon:'path://M623.14 848.54a24.71 24.71 0 0 1-8.9-1.64c-7.25-2.81-11.87-8.79-11.87-15.36V193.31c0-9.39 9.3-17 20.77-17s20.77 7.61 20.77 17v602.36l183.16-122.61c8.88-5.94 22-4.87 29.23 2.39s6 18-2.92 23.92L636.29 844.69a23.8 23.8 0 0 1-13.15 3.85zM400.86 847.68c-11.47 0-20.77-7.6-20.77-17V228.33L196.93 350.94c-8.88 5.94-22 4.87-29.23-2.39s-6-18 2.92-23.92l217.09-145.32a24.57 24.57 0 0 1 22.05-2.21c7.25 2.81 11.87 8.79 11.87 15.36v638.23c0 9.39-9.3 16.99-20.77 16.99z',
                                                    onclick: function (){
                                                        getChart('',parameter,true, false)
                                                    }
                                                }
                                            }
                                        },
                                        grid: {
                                            left: '6%',
                                            right: '6%',
                                            bottom: '3%',
                                            containLabel: true
                                        },
                                        xAxis: {
                                            type: 'category',
                                            boundaryGap: false,
                                            name: visualizationData.xAxis.type,
                                            data: visualizationData.xAxis.data
                                        },
                                        yAxis: {
                                            type: 'value'
                                        },
                                        series: visualizationData.series
                                    };
                                    myChart.setOption(option,true);
                                    break;
                                case 'HISTOGRAM':
                                    $('#chartBar').css('display','block');
                                    // 柱状图
                                    for (var i=0;i<visualizationData.series.length;i++){
                                        visualizationData.series[i].barGap = 0;
                                        for (var key in visualizationData.series[i]){
                                            if (key === 'stack'){
                                                visualizationData.series[i][key] = '';
                                            }
                                        }
                                    }
                                    // visualizationData.xAxis.data = visualizationData.xAxis.data.map(i => parseInt(i, 0));
                                    var chartBar = echarts.init(document.getElementById('chartBar'));
                                    var BarOption = {
                                        color: ['#116979', '#18b0b0', '#00bdaa', '#27496d'],
                                        tooltip: {
                                            trigger: 'axis',
                                            axisPointer: {
                                                type: 'shadow'
                                            }
                                        },
                                        legend: {
                                            data: visualizationData.legend
                                        },
                                        toolbox: {
                                            show: true,
                                            orient: 'vertical',
                                            // left: 'right',
                                            top: 'center',
                                            right: '50',
                                            feature: {
                                                show: false,
                                                mark: {show: true},
                                                dataView: {show: true, readOnly: false},
                                                magicType: {show: true, type: ['stack', 'tiled']},
                                                restore: {show: true},
                                                saveAsImage: {show: true},
                                                myTool1: {
                                                    show: true,
                                                    title: '排序',
                                                    iconStyle: {
                                                        borderColor: '#9f9f9f'
                                                    },
                                                    icon:'path://M623.14 848.54a24.71 24.71 0 0 1-8.9-1.64c-7.25-2.81-11.87-8.79-11.87-15.36V193.31c0-9.39 9.3-17 20.77-17s20.77 7.61 20.77 17v602.36l183.16-122.61c8.88-5.94 22-4.87 29.23 2.39s6 18-2.92 23.92L636.29 844.69a23.8 23.8 0 0 1-13.15 3.85zM400.86 847.68c-11.47 0-20.77-7.6-20.77-17V228.33L196.93 350.94c-8.88 5.94-22 4.87-29.23-2.39s-6-18 2.92-23.92l217.09-145.32a24.57 24.57 0 0 1 22.05-2.21c7.25 2.81 11.87 8.79 11.87 15.36v638.23c0 9.39-9.3 16.99-20.77 16.99z',
                                                    onclick: function (){
                                                        getChart('',parameter,true, false)
                                                    }
                                                }
                                            }
                                        },
                                        xAxis: [
                                            {
                                                type: 'category',
                                                axisTick: {show: false},
                                                name: visualizationData.xAxis.type,
                                                // axisLabel:{
                                                //     interval:0,
                                                //     rotate:45,
                                                //     margin:2,
                                                //     textStyle:{
                                                //         color:"#8f8f8f"
                                                //     }
                                                // },
                                                data: visualizationData.xAxis.data
                                            }
                                        ],

                                        yAxis: [
                                            {
                                                type: 'value'
                                            }
                                        ],
                                        series: visualizationData.series
                                    };
                                    chartBar.setOption(BarOption,true);
                                    break;
                                case 'SCATTERPLOT':
                                    $('#chartScatter').css('display','block');
                                    $('#preId').css('background','#404a59');

                                    // 散点图
                                    var chartScatter = echarts.init(document.getElementById('chartScatter'));
                                    var schema = visualizationData.schema;
                                    // var itemStyle = {
                                    //     opacity: 0.8,
                                    //     shadowBlur: 10,
                                    //     shadowOffsetX: 0,
                                    //     shadowOffsetY: 0,
                                    //     shadowColor: 'rgba(0, 0, 0, 0.5)'
                                    // };
                                    var ScatterOption = {
                                        backgroundColor: '#404a59',
                                        color: [
                                            '#fe5d4e', '#43c2f7', '#ffa61b', '#64d290', '#cf27bd', '#707ad9'
                                        ],
                                        legend: {
                                            top: 10,
                                            data: visualizationData.legend,
                                            textStyle: {
                                                color: '#fff',
                                                fontSize: 16
                                            }
                                        },
                                        grid: {
                                            left: '10%',
                                            right: 150,
                                            top: '18%',
                                            bottom: '10%'
                                        },
                                        tooltip: {
                                            padding: 10,
                                            backgroundColor: '#222',
                                            borderColor: '#777',
                                            borderWidth: 1,
                                            formatter: function (obj) {
                                                var value = obj.value;
                                                return '<div style="border-bottom: 1px solid rgba(255,255,255,.3); font-size: 18px;padding-bottom: 7px;margin-bottom: 7px">'
                                                    + obj.seriesName + ' ' + value[0] + '日：'
                                                    + value[7]
                                                    + '</div>'
                                                    + schema[1].text + '：' + value[1] + '<br>'
                                                    + schema[2].text + '：' + value[2] + '<br>'
                                                    + schema[3].text + '：' + value[3] + '<br>'
                                                    + schema[4].text + '：' + value[4] + '<br>'
                                                    + schema[5].text + '：' + value[5] + '<br>'
                                                    + schema[6].text + '：' + value[6] + '<br>';
                                            }
                                        },
                                        xAxis: {
                                            type: 'value',
                                            name: '日期',
                                            nameGap: 16,
                                            nameTextStyle: {
                                                color: '#fff',
                                                fontSize: 14
                                            },
                                            max: 31,
                                            splitLine: {
                                                show: false
                                            },
                                            axisLine: {
                                                lineStyle: {
                                                    color: '#eee'
                                                }
                                            }
                                        },
                                        yAxis: {
                                            type: 'value',
                                            name: 'AQI指数',
                                            nameLocation: 'end',
                                            nameGap: 20,
                                            nameTextStyle: {
                                                color: '#fff',
                                                fontSize: 16
                                            },
                                            axisLine: {
                                                lineStyle: {
                                                    color: '#eee'
                                                }
                                            },
                                            splitLine: {
                                                show: false
                                            }
                                        },
                                        toolbox: {
                                            right: '50',
                                            feature: {
                                                saveAsImage: {
                                                    iconStyle:{
                                                        emphasis:{
                                                            color: '#ffffff',
                                                        },
                                                        normal: {
                                                            color: '#ffffff',
                                                            borderColor: '#ffffff',
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        visualMap: [
                                            {
                                                right: '50',
                                                top: '10%',
                                                dimension: 2,
                                                min: 0,
                                                max: 260,
                                                itemWidth: 30,
                                                itemHeight: 120,
                                                calculable: true,
                                                precision: 0.1,
                                                text: ['圆形大小：'],
                                                textGap: 30,
                                                textStyle: {
                                                    color: '#fff'
                                                },
                                                inRange: {
                                                    symbolSize: [10, 70]
                                                },
                                                outOfRange: {
                                                    symbolSize: [10, 70],
                                                    color: ['rgba(255,255,255,.2)']
                                                },
                                                controller: {
                                                    inRange: {
                                                        color: ['#fe5d4e']
                                                    },
                                                    outOfRange: {
                                                        color: ['#444']
                                                    }
                                                }
                                            },
                                            {
                                                right: '50',
                                                bottom: '2%',
                                                dimension: 6,
                                                min: 0,
                                                max: 50,
                                                itemHeight: 120,

                                                precision: 0.1,
                                                text: ['明暗：数据'],
                                                textGap: 30,
                                                textStyle: {
                                                    color: '#fff'
                                                },
                                                inRange: {
                                                    colorLightness: [1, 0.5]
                                                },
                                                outOfRange: {
                                                    color: ['rgba(255,255,255,.2)']
                                                },
                                                controller: {
                                                    inRange: {
                                                        color: ['#fe5d4e']
                                                    },
                                                    outOfRange: {
                                                        color: ['#444']
                                                    }
                                                }
                                            }
                                        ],
                                        series: visualizationData.series
                                    };
                                    chartScatter.setOption(ScatterOption,true);

                                    break;
                                case 'TABLE':
                                    // 表格
                                    // var dataColumns = [
                                    //     {title: 'idKey'}
                                    // ];
                                    //
                                    // visualizationData.schema.forEach((item)=>{
                                    //     dataColumns.push({title: item});
                                    //
                                    // })
                                    // var staData = [{"m4":"1112994.00","name":"面上项目"},{"m4":"216527.00","name":"重点项目"},{"m4":"158278.76","name":"重大项目"},{"m4":"75000.00","name":"优秀青年科学基金项目"},{"m4":"87399.96","name":"重大研究计划"},{"m4":"116920.00","name":"国家杰出青年科学基金"},{"m4":"36010.00","name":"创新研究群体项目"},{"m4":"97459.57","name":"国际(地区)合作与交流项目"},{"m4":"94494.78","name":"国家重大科研仪器研制项目"},{"m4":"238750.40","name":"联合基金项目"},{"m4":"435608.00","name":"青年科学基金项目"},{"m4":"110738.00","name":"地区科学基金项目"},{"m4":"77000.00","name":"科学中心项目"},{"m4":"4500.00","name":"数学天元基金项目"},{"m4":"47710.18","name":"专项项目"}];
                                    // $('#chartTable').css('display','block');
                                    // var dataSet = [];
                                    // var temp = [];
                                    // visualizationData.data.forEach((value,index)=>{ //数组循环
                                    //     temp.push(i + 1);
                                    //     for(var key in value){
                                    //         temp.push(value[key]);
                                    //     }
                                    //     dataSet.push(temp);
                                    //     temp = [];
                                    // })
                                    // $('#statisticsTableMode').DataTable({
                                    //     data: dataSet,
                                    //     columns: dataColumns,
                                    //     "paging": false,
                                    //     "destroy": true,
                                    //     "bAutoWidth": false,  // 禁止自适应宽度
                                    //     "order": [[0, "asc"]],
                                    //     "columnDefs": [
                                    //         { "visible": false, "targets": [0]}
                                    //     ],
                                    //     oLanguage: {
                                    //         "sLengthMenu": "每页显示 _MENU_ 条记录",
                                    //         "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
                                    //         "sInfoEmpty": "没有数据",
                                    //         "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
                                    //         "sZeroRecords": "没有检索到数据",
                                    //         "sSearch": "查询:",
                                    //         "oPaginate": {
                                    //             "sFirst": "首页",
                                    //             "sPrevious": "前一页",
                                    //             "sNext": "后一页",
                                    //             "sLast": "尾页"
                                    //         }
                                    //     },
                                    //     dom: 'lBfrtip',
                                    //     "buttons": [
                                    //         {
                                    //             extend: 'excelHtml5',
                                    //             text: "导出Excel",
                                    //             className: "btn-sm",
                                    //             customize: function ( xlsx ) {
                                    //                 var sheet = xlsx.xl.worksheets['sheet1.xml'];
                                    //                 // $('row c[r^="C"]', sheet).attr( 's', '2' );
                                    //                 $('c[r=A1] t', sheet).text('      金额单位：万元');
                                    //             }
                                    //         }
                                    //     ]
                                    // });
                                    break;
                                default:
                                    break;
                            }
                        }
                    });
                }else if (parameter.isSoft || parameter.isSoft===false){
                    switch (type){
                        case 'PIECHART':
                            // 饼状图
                            $('#chartPie').css('display','block');
                            var newArr = [];
                            for(var i=0;i<visualizationData.legend.length;i++){
                                newArr.push(Number(visualizationData.legend[i]))
                            }
                            var chartPie = echarts.init(document.getElementById('chartPie'));
                            var PieOption = {
                                color: ['#726a95', '#709fb0', '#a0c1b8', '#f4ebc1', '#e4e4e4', '#ad6989', '#f9d89c', '#7fdbda', '#ba7967', '#e2979c', '#abc2e8'],
                                // title: {
                                //     text: '',
                                //     subtext: '',
                                //     left: 'center'
                                // },
                                tooltip: {
                                    trigger: 'item',
                                    formatter: '{a} <br/>{b} : {c} ({d}%)'
                                },
                                legend: {
                                    // orient: 'vertical',
                                    top: 10,
                                    left: 'center',
                                    data: newArr
                                },
                                toolbox: {
                                    right: '50',
                                    feature: {
                                        saveAsImage: {}
                                    }
                                },
                                series: [
                                    {
                                        name: '访问来源',
                                        type: 'pie',
                                        radius: '55%',
                                        center: ['50%', '60%'],
                                        selectedMode: 'single',
                                        data: visualizationData.series,
                                        emphasis: {
                                            itemStyle: {
                                                shadowBlur: 10,
                                                shadowOffsetX: 0,
                                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                                            }
                                        }
                                    }
                                ]
                            };
                            chartPie.setOption(PieOption,true);
                            break;
                        case 'LINECHART':
                            $('#chartLine').css('display','block');
                            for (var i=0;i<visualizationData.series.length;i++){
                                // visualizationData.series[i].areaStyle = {};
                                visualizationData.series[i].smooth = true;
                                for (var key in visualizationData.series[i]){
                                    if (key === 'stack'){
                                        visualizationData.series[i][key] = 'count';
                                    }
                                }
                            }
                            // visualizationData.xAxis.data = visualizationData.xAxis.data.map(i => parseInt(i, 0));
                            // 折线图
                            var myChart = echarts.init(document.getElementById('chartLine'));
                            var option = {
                                title: {
                                    text: ''
                                },
                                color: ['#879DDA', '#9FE080', '#FDD963', '#F86C6C', '#ad6989', '#40B27D', '#FE9059', '#A76AC3'],
                                tooltip: {
                                    trigger: 'axis',
                                    axisPointer: {
                                        type: 'cross',
                                        label: {
                                            backgroundColor: '#6a7985'
                                        }
                                    }
                                },
                                legend: {
                                    data: visualizationData.legend
                                },
                                toolbox: {
                                    right: '50',
                                    feature: {
                                        show: false,
                                        saveAsImage: {},
                                        myTool1: {
                                            show: true,
                                            title: '排序',
                                            iconStyle: {
                                                borderColor: '#9f9f9f'
                                            },
                                            icon:'path://M623.14 848.54a24.71 24.71 0 0 1-8.9-1.64c-7.25-2.81-11.87-8.79-11.87-15.36V193.31c0-9.39 9.3-17 20.77-17s20.77 7.61 20.77 17v602.36l183.16-122.61c8.88-5.94 22-4.87 29.23 2.39s6 18-2.92 23.92L636.29 844.69a23.8 23.8 0 0 1-13.15 3.85zM400.86 847.68c-11.47 0-20.77-7.6-20.77-17V228.33L196.93 350.94c-8.88 5.94-22 4.87-29.23-2.39s-6-18 2.92-23.92l217.09-145.32a24.57 24.57 0 0 1 22.05-2.21c7.25 2.81 11.87 8.79 11.87 15.36v638.23c0 9.39-9.3 16.99-20.77 16.99z',
                                            onclick: function (){
                                                getChart('',parameter,false, false)
                                            }
                                        }
                                    }
                                },
                                grid: {
                                    left: '6%',
                                    right: '6%',
                                    bottom: '3%',
                                    containLabel: true
                                },
                                xAxis: {
                                    type: 'category',
                                    boundaryGap: false,
                                    name: visualizationData.xAxis.type,
                                    data: visualizationData.xAxis.data
                                },
                                yAxis: {
                                    type: 'value'
                                },
                                series: visualizationData.series
                            };
                            myChart.setOption(option,true);
                            break;
                        case 'HISTOGRAM':
                            $('#chartBar').css('display','block');
                            // 柱状图
                            for (var i=0;i<visualizationData.series.length;i++){
                                visualizationData.series[i].barGap = 0;
                                for (var key in visualizationData.series[i]){
                                    if (key === 'stack'){
                                        visualizationData.series[i][key] = '';
                                    }
                                }
                            }
                            // visualizationData.xAxis.data = visualizationData.xAxis.data.map(i => parseInt(i, 0));
                            var chartBar = echarts.init(document.getElementById('chartBar'));
                            var BarOption = {
                                color: ['#116979', '#18b0b0', '#00bdaa', '#27496d'],
                                tooltip: {
                                    trigger: 'axis',
                                    axisPointer: {
                                        type: 'shadow'
                                    }
                                },
                                legend: {
                                    data: visualizationData.legend
                                },
                                toolbox: {
                                    show: true,
                                    orient: 'vertical',
                                    // left: 'right',
                                    top: 'center',
                                    right: '50',
                                    feature: {
                                        show: false,
                                        mark: {show: true},
                                        dataView: {show: true, readOnly: false},
                                        magicType: {show: true, type: ['stack', 'tiled']},
                                        restore: {show: true},
                                        saveAsImage: {show: true},
                                        myTool1: {
                                            show: true,
                                            title: '排序',
                                            iconStyle: {
                                                borderColor: '#9f9f9f'
                                            },
                                            icon:'path://M623.14 848.54a24.71 24.71 0 0 1-8.9-1.64c-7.25-2.81-11.87-8.79-11.87-15.36V193.31c0-9.39 9.3-17 20.77-17s20.77 7.61 20.77 17v602.36l183.16-122.61c8.88-5.94 22-4.87 29.23 2.39s6 18-2.92 23.92L636.29 844.69a23.8 23.8 0 0 1-13.15 3.85zM400.86 847.68c-11.47 0-20.77-7.6-20.77-17V228.33L196.93 350.94c-8.88 5.94-22 4.87-29.23-2.39s-6-18 2.92-23.92l217.09-145.32a24.57 24.57 0 0 1 22.05-2.21c7.25 2.81 11.87 8.79 11.87 15.36v638.23c0 9.39-9.3 16.99-20.77 16.99z',
                                            onclick: function (){
                                                getChart('',parameter,false, false)
                                            }
                                        }
                                    }
                                },
                                xAxis: [
                                    {
                                        type: 'category',
                                        axisTick: {show: false},
                                        name: visualizationData.xAxis.type,
                                        // axisLabel:{
                                        //     interval:0,
                                        //     rotate:45,
                                        //     margin:2,
                                        //     textStyle:{
                                        //         color:"#8f8f8f"
                                        //     }
                                        // },
                                        data: visualizationData.xAxis.data
                                    }
                                ],

                                yAxis: [
                                    {
                                        type: 'value'
                                    }
                                ],
                                series: visualizationData.series
                            };
                            chartBar.setOption(BarOption,true);
                            break;
                        case 'SCATTERPLOT':
                            $('#chartScatter').css('display','block');
                            $('#preId').css('background','#404a59');

                            // 散点图
                            var chartScatter = echarts.init(document.getElementById('chartScatter'));
                            var schema = visualizationData.schema;
                            // var itemStyle = {
                            //     opacity: 0.8,
                            //     shadowBlur: 10,
                            //     shadowOffsetX: 0,
                            //     shadowOffsetY: 0,
                            //     shadowColor: 'rgba(0, 0, 0, 0.5)'
                            // };
                            var ScatterOption = {
                                backgroundColor: '#404a59',
                                color: [
                                    '#fe5d4e', '#43c2f7', '#ffa61b', '#64d290', '#cf27bd', '#707ad9'
                                ],
                                legend: {
                                    top: 10,
                                    data: visualizationData.legend,
                                    textStyle: {
                                        color: '#fff',
                                        fontSize: 16
                                    }
                                },
                                grid: {
                                    left: '10%',
                                    right: 150,
                                    top: '18%',
                                    bottom: '10%'
                                },
                                tooltip: {
                                    padding: 10,
                                    backgroundColor: '#222',
                                    borderColor: '#777',
                                    borderWidth: 1,
                                    formatter: function (obj) {
                                        var value = obj.value;
                                        return '<div style="border-bottom: 1px solid rgba(255,255,255,.3); font-size: 18px;padding-bottom: 7px;margin-bottom: 7px">'
                                            + obj.seriesName + ' ' + value[0] + '日：'
                                            + value[7]
                                            + '</div>'
                                            + schema[1].text + '：' + value[1] + '<br>'
                                            + schema[2].text + '：' + value[2] + '<br>'
                                            + schema[3].text + '：' + value[3] + '<br>'
                                            + schema[4].text + '：' + value[4] + '<br>'
                                            + schema[5].text + '：' + value[5] + '<br>'
                                            + schema[6].text + '：' + value[6] + '<br>';
                                    }
                                },
                                xAxis: {
                                    type: 'value',
                                    name: '日期',
                                    nameGap: 16,
                                    nameTextStyle: {
                                        color: '#fff',
                                        fontSize: 14
                                    },
                                    max: 31,
                                    splitLine: {
                                        show: false
                                    },
                                    axisLine: {
                                        lineStyle: {
                                            color: '#eee'
                                        }
                                    }
                                },
                                yAxis: {
                                    type: 'value',
                                    name: 'AQI指数',
                                    nameLocation: 'end',
                                    nameGap: 20,
                                    nameTextStyle: {
                                        color: '#fff',
                                        fontSize: 16
                                    },
                                    axisLine: {
                                        lineStyle: {
                                            color: '#eee'
                                        }
                                    },
                                    splitLine: {
                                        show: false
                                    }
                                },
                                toolbox: {
                                    right: '50',
                                    feature: {
                                        saveAsImage: {
                                            iconStyle:{
                                                emphasis:{
                                                    color: '#ffffff',
                                                },
                                                normal: {
                                                    color: '#ffffff',
                                                    borderColor: '#ffffff',
                                                }
                                            }
                                        }
                                    }
                                },
                                visualMap: [
                                    {
                                        right: '50',
                                        top: '10%',
                                        dimension: 2,
                                        min: 0,
                                        max: 260,
                                        itemWidth: 30,
                                        itemHeight: 120,
                                        calculable: true,
                                        precision: 0.1,
                                        text: ['圆形大小：'],
                                        textGap: 30,
                                        textStyle: {
                                            color: '#fff'
                                        },
                                        inRange: {
                                            symbolSize: [10, 70]
                                        },
                                        outOfRange: {
                                            symbolSize: [10, 70],
                                            color: ['rgba(255,255,255,.2)']
                                        },
                                        controller: {
                                            inRange: {
                                                color: ['#fe5d4e']
                                            },
                                            outOfRange: {
                                                color: ['#444']
                                            }
                                        }
                                    },
                                    {
                                        right: '50',
                                        bottom: '2%',
                                        dimension: 6,
                                        min: 0,
                                        max: 50,
                                        itemHeight: 120,

                                        precision: 0.1,
                                        text: ['明暗：数据'],
                                        textGap: 30,
                                        textStyle: {
                                            color: '#fff'
                                        },
                                        inRange: {
                                            colorLightness: [1, 0.5]
                                        },
                                        outOfRange: {
                                            color: ['rgba(255,255,255,.2)']
                                        },
                                        controller: {
                                            inRange: {
                                                color: ['#fe5d4e']
                                            },
                                            outOfRange: {
                                                color: ['#444']
                                            }
                                        }
                                    }
                                ],
                                series: visualizationData.series
                            };
                            chartScatter.setOption(ScatterOption,true);

                            break;
                        case 'TABLE':
                            // 表格
                            // var dataColumns = [
                            //     {title: 'idKey'}
                            // ];
                            //
                            // visualizationData.schema.forEach((item)=>{
                            //     dataColumns.push({title: item});
                            //
                            // })
                            // var staData = [{"m4":"1112994.00","name":"面上项目"},{"m4":"216527.00","name":"重点项目"},{"m4":"158278.76","name":"重大项目"},{"m4":"75000.00","name":"优秀青年科学基金项目"},{"m4":"87399.96","name":"重大研究计划"},{"m4":"116920.00","name":"国家杰出青年科学基金"},{"m4":"36010.00","name":"创新研究群体项目"},{"m4":"97459.57","name":"国际(地区)合作与交流项目"},{"m4":"94494.78","name":"国家重大科研仪器研制项目"},{"m4":"238750.40","name":"联合基金项目"},{"m4":"435608.00","name":"青年科学基金项目"},{"m4":"110738.00","name":"地区科学基金项目"},{"m4":"77000.00","name":"科学中心项目"},{"m4":"4500.00","name":"数学天元基金项目"},{"m4":"47710.18","name":"专项项目"}];
                            // $('#chartTable').css('display','block');
                            // var dataSet = [];
                            // var temp = [];
                            // visualizationData.data.forEach((value,index)=>{ //数组循环
                            //     temp.push(i + 1);
                            //     for(var key in value){
                            //         temp.push(value[key]);
                            //     }
                            //     dataSet.push(temp);
                            //     temp = [];
                            // })
                            // $('#statisticsTableMode').DataTable({
                            //     data: dataSet,
                            //     columns: dataColumns,
                            //     "paging": false,
                            //     "destroy": true,
                            //     "bAutoWidth": false,  // 禁止自适应宽度
                            //     "order": [[0, "asc"]],
                            //     "columnDefs": [
                            //         { "visible": false, "targets": [0]}
                            //     ],
                            //     oLanguage: {
                            //         "sLengthMenu": "每页显示 _MENU_ 条记录",
                            //         "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条数据",
                            //         "sInfoEmpty": "没有数据",
                            //         "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
                            //         "sZeroRecords": "没有检索到数据",
                            //         "sSearch": "查询:",
                            //         "oPaginate": {
                            //             "sFirst": "首页",
                            //             "sPrevious": "前一页",
                            //             "sNext": "后一页",
                            //             "sLast": "尾页"
                            //         }
                            //     },
                            //     dom: 'lBfrtip',
                            //     "buttons": [
                            //         {
                            //             extend: 'excelHtml5',
                            //             text: "导出Excel",
                            //             className: "btn-sm",
                            //             customize: function ( xlsx ) {
                            //                 var sheet = xlsx.xl.worksheets['sheet1.xml'];
                            //                 // $('row c[r^="C"]', sheet).attr( 's', '2' );
                            //                 $('c[r=A1] t', sheet).text('      金额单位：万元');
                            //             }
                            //         }
                            //     ]
                            // });
                            break;
                        default:
                            break;
                    }
                }
            }
        }
    });
}