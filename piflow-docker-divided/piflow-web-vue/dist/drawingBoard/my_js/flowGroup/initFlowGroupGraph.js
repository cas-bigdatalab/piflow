// Extends EditorUi to update I/O action states based on availability of backend
var graphGlobal = null;
var thisEditor = null;
var sign = true;
var flag = 0;
var index = true;
var consumedFlag, removeGroupPaths;
var parentsId = null;
var imgType = null;

function initFlowGroupDrawingBoardData(loadId, parentAccessPath, backFunc) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        type: "get",
        url: "/flowGroup/drawingBoardData",
        async: false,
        data: {
            load: loadId,
            parentAccessPath: parentAccessPath
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                if (dataMap.parentsId) {
                    parentsId = dataMap.parentsId;
                } else {
                    parentsId = 'null';
                }
                let herf = top.window.location.href.split("src=")[1];
                if (herf.indexOf('BreadcrumbSchedule') !== -1) {
                    top.document.getElementById('BreadcrumbSchedule').style.display = 'block';
                    top.document.getElementById('BreadcrumbGroup').style.display = 'none';
                } else {
                    top.document.getElementById('BreadcrumbGroup').style.display = 'block';
                    top.document.getElementById('BreadcrumbSchedule').style.display = 'none';
                }
                top.document.getElementById('BreadcrumbFlow').style.display = 'none';
                top.document.getElementById('BreadcrumbProcess').style.display = 'none';
                top.document.getElementById('BreadcrumbProcessGroup').style.display = 'none';
                var link = top.document.getElementById('GroupParents');
                if (parentsId !== 'null') {
                    link.style.display = 'inline-block';
                    link.href = '#/drawingBoard?src=/drawingBoard/page/flowGroup/mxGraph/index.html?drawingBoardType=GROUP&parentAccessPath=flowGroupList&load=' + parentsId;
                } else {
                    link.style.display = 'none';
                }
                xmlDate = dataMap.xmlDate;
                maxStopPageId = dataMap.maxStopPageId;
                isExample = dataMap.isExample;
                if (dataMap.mxGraphComponentList) {
                    var mxGraphComponentList = dataMap.mxGraphComponentList;
                    for (var index = 0; index < mxGraphComponentList.length; index++) {
                        var component_prefix = mxGraphComponentList[index].component_prefix
                        if (component_prefix.indexOf("/piflow-web/") > -1) {
                            component_prefix = component_prefix.replace('/piflow-web', web_header_prefix)
                        }
                        mxGraphComponentList[index].component_prefix = component_prefix
                    }
                    Sidebar.prototype.component_data = mxGraphComponentList
                }
            } else {
                window_location_href("/page/error/errorPage.html");
            }
            if (backFunc && $.isFunction(backFunc)) {
                backFunc(data);
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        },
        error: function (request) {//Operation after request failure
            window_location_href("/page/error/errorPage.html");
            return;
        }
    });
}

function imageAjax() {
    var loading
    ajaxRequest({
        type: "post",//Request type post
        url: "/mxGraph/nodeImageList",
        data: {imageType: imgType},
        async: true,//Synchronous Asynchronous
        error: function (request) {//Operation after request failure
            return;
        },
        beforeSend: function () {
            loading = layer.load(0, {
                shade: false,
                success: function (layerContentStyle) {
                    layerContentStyle.find('.layui-layer-content').css({
                        'padding-top': '35px',
                        'text-align': 'left',
                        'width': '120px',
                    });
                },
                icon: 2,
                // time: 100*1000
            });
        },
        success: function (data) {//After the request is successful
            layer.close(loading)
            var nowimage = $("#nowimage")[0];
            nowimage.innerHTML = "";
            var nodeImageList = JSON.parse(data).nodeImageList;
            nodeImageList.forEach(item => {
                var div = document.createElement("div");
                div.className = "imgwrap";
                var image = document.createElement("img");
                image.className = "imageimg"
                image.style = "width:100%;height:100%";
                console.log("-------------------------------");
                image.src = web_header_prefix + (item.imageUrl.replace("/piflow-web", ""));

                div.appendChild(image);
                nowimage.appendChild(div);
                div.onclick = function (e) {
                    e.stopPropagation();
                    for (var i = 0; i < imgwrap1.length; i++) {
                        imgwrap1[i].style.backgroundColor = "#fff"
                    }
                    e.srcElement.style = "background-color:#009688;width:100%;height:100%"
                    imagSrc = e.srcElement.src
                }
            })
            var imgwrap1 = $(".imageimg")

        }
    });
}

function updateMxGraphCellImage(cellEditor, selState, newValue, fn) {
    //   Change picture
    layui.use('upload', function () {
        var upload = layui.upload;
        var loading
        //执行实例
        var uploadInst = upload.render({
            elem: '#uploadimage' //绑定元素
            , url: web_header_prefix + '/mxGraph/uploadNodeImage' //上传接口
            , headers: {
                Authorization: ("Bearer " + token)
            }
            , before: function (obj) {
                this.data = {imageType: "GROUP"};
                loading = layer.load(0, {
                    shade: false,
                    success: function (layerContentStyle) {
                        layerContentStyle.find('.layui-layer-content').css({
                            'padding-top': '35px',
                            'text-align': 'left',
                            'width': '120px',
                        });
                    },
                    icon: 2,
                    // time: 100*1000
                });
            }
            , done: function (res) {
                //上传完毕回调
                console.log("upload success")
                imageAjax();
                layer.close(loading);
            }
            , error: function () {
                //请求异常回调
                console.log("upload error")
            }
        });
    });
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">已有现存可选择更改的图片</span>',
        shadeClose: true,
        shade: 0.3,
        closeBtn: 1,
        shift: 7,
        btn: ['YES', 'NO'],
        area: ['620px', '520px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: $("#changeimage"),
        success: function () {
            imageAjax()
        },
        //YES BUTTON
        btn1: function (index, layero) {
            var newValue = imagSrc;
            imagSrc = null
            EditorUi.prototype.saveImageUpdate(cellEditor, selState, newValue, fn, 66, 66);
            layer.close(index)
            setTimeout(() => {
                saveXml(null, "MOVED")
            }, 300)

        },
        //NO BUTTON
        btn2: function (index, layero) {
            imagSrc = null
            layer.close(index)
        },
        //close function
        cancel: function (index, layero) {
            layer.close(index)
            return false;
        }
    });
}

function initFlowGroupGraph() {
    Format.prototype.isShowTextCell = true;
    Menus.prototype.customRightMenu = ['runAll'];
    Menus.prototype.customCellRightMenu = ['run'];
    EditorUi.prototype.customUpdeteImg = updateMxGraphCellImage;
    Actions.prototype.RunAll = runFlowGroup;
    Actions.prototype.RunCells = RunFlowOrFlowGroupCells;
    EditorUi.prototype.saveGraphData = saveXml;
    Graph.prototype.errorToast = toastErrorMsg;
    Format.hideSidebar(true, true);
    Format.customizeType = "GROUP";
    var editorUiInit = EditorUi.prototype.init;
    $("#right-group-wrap")[0].style.display = "block";

    EditorUi.prototype.init = function () {
        editorUiInit.apply(this, arguments);
        graphGlobal = this.editor.graph;
        thisEditor = this.editor;
        this.actions.get('export').setEnabled(false);
        //Monitoring event
        graphGlobal.addListener(mxEvent.CELLS_ADDED, function (sender, evt) {
            if (isExample) {
                prohibitEditing(evt, 'ADD');
            } else {
                addMxCellOperation(evt);
            }
        });
        graphGlobal.addListener(mxEvent.CELLS_MOVED, function (sender, evt) {
            if (isExample) {
                prohibitEditing(evt, 'MOVED');
            } else {
                movedMxCellOperation(evt);
            }
        });
        graphGlobal.addListener(mxEvent.CELLS_REMOVED, function (sender, evt) {
            if (isExample) {
                prohibitEditing(evt, 'REMOVED');
            } else {
                removeMxCellOperation(evt);
            }
        });

        graphGlobal.addListener(mxEvent.CLICK, function (sender, evt) {
            consumedFlag = evt.consumed ? true : false;
            mxEventClickFunc(evt.properties.cell, consumedFlag);
        });
        graphGlobal.addListener(mxEvent.DOUBLE_CLICK, function (sender, evt) {
            openProcessMonitor(evt);
            if (evt.properties.cell.style && (evt.properties.cell.style).indexOf("text\;") === 0) {
                if (graphGlobal.isEnabled()) {
                    graphGlobal.startEditingAtCell();
                }
            }
        });
        loadXml(xmlDate);
        // Disconnect cell On Move
        graphGlobal.setDisconnectOnMove(false);
        // Not Allow Loop connection
        graphGlobal.setAllowLoops(false);
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
    EditorUi.prototype.menubarHeight = 48;
    EditorUi.prototype.menubarShow = false;
    EditorUi.prototype.customToobar = true;
    ClickSlider();
}

//mxGraph click event
function mxEventClickFunc(cell, consumedFlag) {
    $("#flowGroup_info_inc_id").hide();
    $("#flowGroup_path_inc_id").hide();
    $("#flowGroup_property_inc_id").hide();
    if (index) {
        $(".right-group").toggleClass("open-right");
        $(".ExpandSidebar").toggleClass("ExpandSidebar-open");
        $(".triggerSlider i").removeClass("fa fa-angle-left fa-2x ").toggleClass("fa fa-angle-right fa-2x");
        index = false
    }
    if (!consumedFlag) {
        $("#flowGroup_info_inc_id").show();
        // info
        queryFlowGroupInfo(loadId);
        return;
    }
    var cells_arr = graphGlobal.getSelectionCells();
    if (cells_arr.length !== 1) {
        $("#flowGroup_info_inc_id").show();
        // info
        queryFlowGroupInfo(loadId);
    } else {
        var selectedCell = cells_arr[0]
        if (selectedCell && (selectedCell.edge === 1 || selectedCell.edge)) {
            $("#flowGroup_path_inc_id").show();
            queryPathInfo(selectedCell.id, loadId)
        } else if (selectedCell && selectedCell.style && (selectedCell.style).indexOf("image\;") === 0) {
            $("#flowGroup_property_inc_id").show();
            queryFlowOrFlowGroupProperty(selectedCell.id, loadId);
        } else if (selectedCell && selectedCell.style && (selectedCell.style).indexOf("text\;") === 0) {
            $("#flowGroup_info_inc_id").show();
            // info
            queryFlowGroupInfo(loadId);
        }
    }
}

//Erase drawing board records
function eraseRecord() {
    thisEditor.lastSnapshot = new Date().getTime();
    thisEditor.undoManager.clear();
    thisEditor.ignoredChanges = 0;
    thisEditor.setModified(false);
}

function selectCellByPageId(pageId, isClick) {
    if (!pageId) {
        return;
    }
    var s_cell = graphGlobal.getModel().getCell(pageId);
    graphGlobal.addSelectionCell(s_cell);
    if (isClick) {
        mxEventClickFunc(s_cell, true);
    }
}

//load xml file
function loadXml(loadStr) {
    if (!loadStr) {
        return;
    }
    loadStr = replaceImageHead(loadStr, 'img');
    loadStr = replaceImageHead(loadStr, 'images');
    var xml = mxUtils.parseXml(loadStr);
    var node = xml.documentElement;
    var dec = new mxCodec(node.ownerDocument);
    dec.decode(node, graphGlobal.getModel());
    eraseRecord();
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
    loadDate = loadDate.replace(new RegExp("/img/flow_01_128x128.png","g"),"/img/task/task.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_02_128x128.png","g"),"/img/task/task1.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_03_128x128.png","g"),"/img/task/task2.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_04_128x128.png","g"),"/img/task/task3.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_05_128x128.png","g"),"/img/task/task4.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_06_128x128.png","g"),"/img/task/task5.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_07_128x128.png","g"),"/img/task/task6.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_08_128x128.png","g"),"/img/task/task7.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_09_128x128.png","g"),"/img/task/task8.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_10_128x128.png","g"),"/img/task/task.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_11_128x128.png","g"),"/img/task/task1.png");
    loadDate = loadDate.replace(new RegExp("/img/flow_12_128x128.png","g"),"/img/task/task2.png");
    return loadDate;
}

// add node
function addMxCellOperation(evt) {
    var cells = evt.properties.cells;

    var cellArrayRemove = [];
    var cellArrayAdd = [];

    cells.forEach(cellFor => {
        if (cellFor && cellFor.edge) {
            var cellForSource = cellFor.source;
            var cellForTarget = cellFor.target;

            if (!cellForSource || !cellForTarget) {
                cellArrayRemove.push(cellFor);
                return;
            }
            if (!cellForSource.style || !cellForTarget.style) {
                cellArrayRemove.push(cellFor);
                return;
            }
            if ((cellForSource.style).indexOf("text\;") === 0 || (cellForTarget.style).indexOf("text\;") === 0) {
                cellArrayRemove.push(cellFor);
                return;
            }
            cellArrayAdd.push(cellFor);
        } else {
            cellArrayAdd.push(cellFor);
        }
    });
    var mxCellArrayAdd = [];
    cellArrayAdd.forEach(cellFor => {
        var mxCellAdd = graphCellToMxCellVo(cellFor);
        if (mxCellAdd) {
            mxCellArrayAdd.push(mxCellAdd);
        }
    });
    graphGlobal.removeCells(cellArrayRemove);
    if (cells.length != cellArrayRemove.length) {
        ajaxRequest({
            cache: true,//Keep cached data
            type: "POST",//Request type post
            url: "/mxGraph/addMxCellAndData",
            data: JSON.stringify({
                mxCellVoList: mxCellArrayAdd,
                loadId: loadId
            }),
            contentType: 'application/json;charset=utf-8',
            async: true,//Synchronous Asynchronous
            error: function (request) {//Operation after request failure
                layer.msg('Add failed, refresh page after 1 second', {icon: 2, shade: 0, time: 2000}, function () {
                    graphGlobal.removeCells(cellArrayAdd);
                    //window.location.reload();
                });
                return;
            },
            success: function (data) {//After the request is successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    var addNodeIdAndPageIdList = dataMap.addNodeIdAndPageIdList;
                    var flagA = true;
                    if (addNodeIdAndPageIdList && addNodeIdAndPageIdList.length === 1) {
                        var addNodeIdAndPageId = addNodeIdAndPageIdList[0];
                        if ("flow" === addNodeIdAndPageId.type) {
                            openNewFlowWindow(addNodeIdAndPageId.id, addNodeIdAndPageId.pageId);
                        } else if ("flowGroup" === addNodeIdAndPageId.type) {
                            openNewFlowGroupWindow(addNodeIdAndPageId.id, addNodeIdAndPageId.pageId);
                        }
                    }
                    if (flagA && graphGlobal.isEnabled()) {
                        graphGlobal.startEditingAtCell();
                    }
                    thisEditor.setModified(false);
                    console.log("Add save success");
                    if ('cellsAdded' == evt.name) {
                        consumedFlag = evt.consumed ? true : false;
                        mxEventClickFunc(evt.properties.cell, consumedFlag);
                    }
                } else {
                    layer.msg("Add save fail", {icon: 2, shade: 0, time: 2000});
                    console.log("Add save fail");
                    // $('#fullScreen').hide();
                    window.parent.postMessage(false);
                }
            }

        });
    }
}

// del node
function removeMxCellOperation(evt) {
    saveXml(null, 'REMOVED');
}

// moved node
function movedMxCellOperation(evt) {
    if (evt.properties.disconnect) {
        saveXml(null, 'MOVED');   // preservation method
    }
}

// example operation
function prohibitEditing(evt, operationType) {
    if ('ADD' === operationType || 'REMOVED' === operationType) {
        layer.msg("This is an example, you can't add, edit or delete", {
            icon: 2,
            shade: 0,
            time: 2000
        }, function () {

        });
    } else if ('MOVED' === operationType) {
        consumedFlag = evt.consumed ? true : false;
        mxEventClickFunc(evt, consumedFlag);
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/mxGraph/eraseRecord",
        data: {},
        async: true,
        error: function (request) {//Operation after request failure
            if ('ADD' === operationType || 'REMOVED' === operationType) {
                location.reload();
            }
            eraseRecord();
            return;
        },
        success: function (data) {//After the request is successful
            if ('ADD' === operationType || 'REMOVED' === operationType) {
                location.reload();
            }
            eraseRecord();
        }
    });
}

// cell to mxCellVo
function graphCellToMxCellVo(cellObject) {
    if (cellObject) {
        var mxCellVoObject = {};
        mxCellVoObject.pageId = cellObject.id;
        mxCellVoObject.parent = cellObject.parent.id;
        mxCellVoObject.style = cellObject.style;
        mxCellVoObject.value = cellObject.value;
        mxCellVoObject.vertex = cellObject.vertex;
        mxCellVoObject.edge = cellObject.edge;
        if (cellObject.source) {
            mxCellVoObject.source = cellObject.source.id;
        }
        if (cellObject.target) {
            mxCellVoObject.target = cellObject.target.id;
        }
        mxCellVoObject.mxGeometryVo = {};
        if (cellObject.geometry) {
            mxCellVoObject.mxGeometryVo.as = "geometry";
            mxCellVoObject.mxGeometryVo.x = cellObject.geometry.x;
            mxCellVoObject.mxGeometryVo.y = cellObject.geometry.y;
            mxCellVoObject.mxGeometryVo.width = cellObject.geometry.width;
            mxCellVoObject.mxGeometryVo.height = cellObject.geometry.height;
            mxCellVoObject.mxGeometryVo.relative = cellObject.geometry.relative;
        }
        return mxCellVoObject;
    }
    return;
}

//Double click event
function openProcessMonitor(evt) {
    var cellFor = evt.properties.cell;
    if (cellFor.style && (cellFor.style).indexOf("text\;") === 0) {
    } else {
        ajaxRequest({
            cache: true,
            type: "POST",
            url: "/flowGroup/findFlowByGroup",
            data: {"pageId": cellFor.id, "fId": loadId},
            async: true,
            error: function (request) {
                //alert("Jquery Ajax request error!!!");
                return;
            },
            success: function (data) {
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    if ('flow' === dataMap.nodeType) {
                        var flow_obj = dataMap.flowVo;
                        window_location_href("/page/flow/mxGraph/index.html?drawingBoardType=TASK&parentAccessPath=flowGroupList&load=" + flow_obj.id);
                    } else if ('flowGroup' === dataMap.nodeType) {
                        var flowGroup_obj = dataMap.flowGroupVo;
                        // window_location_href("/page/flowGroup/mxGraph/index.html?drawingBoardType=GROUP&parentAccessPath=flowGroupList&parentsId="+ loadId +"&load=" + flowGroup_obj.id);
                        window_location_href("/page/flowGroup/mxGraph/index.html?drawingBoardType=GROUP&parentAccessPath=flowGroupList&load=" + flowGroup_obj.id);
                    }
                } else {
                    console.log(dataMap.errorMsg);
                }
            }
        });
    }
}

//Save XML file and related information
function saveXml(paths, operType) {
    var getXml = thisEditor.getGraphXml();
    var xml_outer_html = getXml.outerHTML;
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/mxGraph/saveDataForGroup",
        //data:$('#loginForm').serialize(),//Serialize the form
        data: {
            imageXML: xml_outer_html,
            load: loadId,
            operType: operType
        },
        async: true,//Synchronous Asynchronous
        error: function (request) {//Operation after request failure
            return;
        },
        success: function (data) {//After the request is successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                console.log(operType + " save success");
                if (graphGlobal.isEnabled()) {
                    graphGlobal.startEditingAtCell();
                }
                thisEditor.setModified(false);

            } else {
                //alert(operType + " save fail");
                layer.msg(operType + " save fail", {icon: 2, shade: 0, time: 2000});
                console.log(operType + " save fail");
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            }

        }

    });
}

//Open new Flow window
function openNewFlowWindow(id, pageId) {
    $("#input_node_flow_id").val(id);
    $("#input_node_flow_pageId").val(pageId);
    $("#flowName").val("");
    $("#description").val("");
    $("#driverMemory").val('1g');
    $("#executorNumber").val('1');
    $("#executorMemory").val('1g');
    $("#executorCores").val('1');
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">Create Flow</span>',
        shadeClose: false,
        shade: 0.3,
        closeBtn: 0,
        shift: 7,
        area: ['580px', '520px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: $("#flow_SubmitPage")
    });
}

//Open new FlowGroup window
function openNewFlowGroupWindow(id, pageId) {
    $("#input_node_flowGroup_id").val(id);
    $("#input_node_flowGroup_pageId").val(pageId);
    $("#flowGroupName").val("");
    $("#flowGroup_description").val("");
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">create flow group</span>',
        shadeClose: false,
        shade: 0.3,
        closeBtn: 0,
        shift: 7,
        area: ['580px', '520px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: $("#flowGroup_SubmitPage")
    });
}

//Query FlowGroup info
function queryFlowGroupInfo(loadId) {
    $("#flowGroup_info_inc_loading").show();
    $("#flowGroup_info_inc_load_fail").hide();
    $("#flowGroup_info_inc_no_data").hide();
    $("#flowGroup_info_inc_load_data").hide();
    ajaxRequest({
        data: {"load": loadId},
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flowGroup/queryFlowGroupData",
        async: true,//Synchronous Asynchronous
        error: function (request) {//Operation after request failure
            $("#flowGroup_info_inc_loading").hide();
            $("#flowGroup_info_inc_load_fail").show();
            return;
        },
        success: function (data) {//After the request is successful
            $("#flowGroup_info_inc_loading").hide();
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var flowGroupVo = dataMap.flowGroupVo;
                if (flowGroupVo) {
                    $("#span_flowGroupVo_id").text(flowGroupVo.id ? flowGroupVo.id : "No content");
                    $("#span_flowGroupVo_name").text(flowGroupVo.name ? flowGroupVo.name : "No content");
                    $("#span_flowGroupVo_description").text(flowGroupVo.description ? flowGroupVo.description : "No content");
                    $("#span_flowGroupVo_crtDttmStr").text(flowGroupVo.crtDttmString ? flowGroupVo.crtDttmString : "No content");
                    $("#span_flowGroupVo_flowsCounts").text(flowGroupVo.flowVoList ? flowGroupVo.flowVoList.length : "0");
                    $("#flowGroup_info_inc_load_data").show();
                } else {
                    $("#flowGroup_info_inc_no_data").show();
                }
            } else {
                $("#flowGroup_info_inc_load_fail").show();
            }
        }
    });
}

//Query Path info
function queryPathInfo(id, loadId) {
    $('#flowGroup_path_inc_loading').show();
    $('#flowGroup_path_inc_load_data').hide();
    $('#flowGroup_path_inc_no_data').hide();
    $('#flowGroup_path_inc_load_fail').hide();
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/flowGroupPath/queryPathInfoFlowGroup",
        data: {"id": id, "fid": loadId},
        async: true,
        error: function (request) {
            //alert("Jquery Ajax request error!!!");
            $('#flowGroup_path_inc_load_fail').show();
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            // console.log(dataMap);
            $('#flowGroup_path_inc_loading').hide();
            if (200 === dataMap.code) {
                //var queryInfo = dataMap.queryInfo;
                var queryInfo = dataMap.queryInfo;
                if (queryInfo) {
                    var flowGroupVo = queryInfo.flowGroupVo;
                    var flowGroupVo_name = flowGroupVo ? flowGroupVo.name : '';
                    $("#span_flowGroupPathVo_flowName").text(flowGroupVo_name);
                    $("#span_flowGroupPathVo_pageId").text(queryInfo.pageId);
                    $("#span_flowGroupPathVo_inport").text(queryInfo.inport);
                    $("#span_flowGroupPathVo_outport").text(queryInfo.outport);
                    $("#span_flowGroupPathVo_from").text(queryInfo.flowFrom);
                    $("#span_flowGroupPathVo_to").text(queryInfo.flowTo);
                    $("#span_flowGroupPathVo_crtDttmStr").text(queryInfo.crtDttmString);
                    $('#flowGroup_path_inc_load_data').show();
                } else {
                    $('#flowGroup_path_inc_no_data').show();
                }
            } else {
                $('#flowGroup_path_inc_load_fail').show();
                console.log("Path attribute query null");
            }
        }
    });
}

// Query Flow or FlowGroup property
function queryFlowOrFlowGroupProperty(pageId, loadId) {
    $('#cell_flowGroup_property_inc_loading').show();
    $('#cell_flowGroup_property_inc_load_fail').hide();
    $('#cell_flowGroup_property_inc_no_data').hide();
    $('#cell_flowGroup_property_inc_load_data').hide();
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/flowGroup/queryIdInfo",
        data: {"fId": loadId, "pageId": pageId},
        async: true,
        error: function (request) {
            $('#cell_flowGroup_property_inc_loading').hide();
            $('#cell_flowGroup_property_inc_load_fail').show();
            return;
        },
        success: function (data) {
            $('#cell_flowGroup_property_inc_loading').hide();
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var nodeType = dataMap.nodeType;
                if ("flowGroup" === nodeType) {
                    var flowGroupVo = dataMap.flowGroupVo;
                    imgType = 'GROUP';
                    $("#div_cell_flowVo_basicInfo_id").hide();
                    $("#div_cell_flowVo_attributeInfo_id").hide();
                    $("#div_cell_flowGroupVo_basicInfo_id").show();
                    $("#div_cell_flowGroupVo_attributeInfo_id").show();

                    // ----------------------- cell flowGroup baseInfo start -----------------------
                    $("#tr_cell_flowGroupVo_name_info").show();
                    $("#tr_cell_flowGroupVo_name_input").hide()
                    $('#input_cell_flowGroupVo_id').val(flowGroupVo.id);
                    $('#input_cell_flowGroupVo_pageId').val(flowGroupVo.pageId);
                    $('#span_cell_flowGroupVo_name').text(flowGroupVo.name);
                    $('#span_cell_flowGroupVo_description').text(flowGroupVo.description);
                    $('#span_cell_flowGroupVo_crtDttmString').text(flowGroupVo.crtDttmString);
                    $('#span_cell_flowGroupVo_flowQuantity').text(flowGroupVo.flowQuantity);
                    $('#span_cell_flowGroupVo_flowGroupQuantity').text(flowGroupVo.flowGroupQuantity);

                    if (isExample) {
                        $('#btn_show_update_group').hide();
                    }
                    // ----------------------- cell flowGroup baseInfo end   -----------------------

                    // ----------------------- cell flowGroup AttributeInfo start -----------------------
                    $('#input_cell_flowGroupVo_description').val(flowGroupVo.description);
                    $('#input_cell_flowGroupVo_description').attr("name", "description");
                    $('#input_cell_flowGroupVo_description').attr("onclick", "openUpdateCellsProperty(this ,'flowGroup')");
                    // ----------------------- cell flowGroup AttributeInfo end -----------------------

                    $('#cell_flowGroup_property_inc_load_data').show();
                } else if ("flow" === nodeType) {
                    var flowVo = dataMap.flowVo;
                    imgType = 'TASK';
                    $("#div_cell_flowGroupVo_basicInfo_id").hide();
                    $("#div_cell_flowGroupVo_attributeInfo_id").hide();
                    $("#div_cell_flowVo_basicInfo_id").show();
                    $("#div_cell_flowVo_attributeInfo_id").show();

                    // ----------------------- cell flow baseInfo start -----------------------
                    $("#tr_cell_flowVo_name_info").show();
                    $("#tr_cell_flowVo_name_input").hide();
                    $('#input_cell_flowVo_id').val(flowVo.id);
                    $('#input_cell_flowVo_pageId').val(flowVo.pageId);
                    $('#span_cell_flowVo_name').text(flowVo.name);
                    $('#span_cell_flowVo_description').text(flowVo.description);
                    $('#span_cell_flowVo_driverMemory').text(flowVo.driverMemory);
                    $('#span_cell_flowVo_executorCores').text(flowVo.executorCores);
                    $('#span_cell_flowVo_executorMemory').text(flowVo.executorMemory);
                    $('#span_cell_flowVo_executorNumber').text(flowVo.executorNumber);
                    $('#span_cell_flowVo_crtDttmString').text(flowVo.crtDttmString);
                    $('#span_cell_flowVo_stopQuantity').text(flowVo.stopQuantity);
                    if (isExample) {
                        $('#btn_show_update').hide();
                    }
                    // ----------------------- cell flow baseInfo end   -----------------------

                    // ----------------------- cell flow AttributeInfo start -----------------------
                    $('#input_cell_flowVo_description').val(flowVo.description);
                    $('#input_cell_flowVo_description').attr("name", "description");
                    $('#input_cell_flowVo_description').attr("onclick", "openUpdateCellsProperty(this ,'flow')");
                    $('#input_cell_flowVo_driverMemory').val(flowVo.driverMemory);
                    $('#input_cell_flowVo_driverMemory').attr("name", "driverMemory");
                    $('#input_cell_flowVo_driverMemory').attr("onclick", "openUpdateCellsProperty(this ,'flow')");
                    $('#input_cell_flowVo_executorCores').val(flowVo.executorCores);
                    $('#input_cell_flowVo_executorCores').attr("name", "executorCores");
                    $('#input_cell_flowVo_executorCores').attr("onclick", "openUpdateCellsProperty(this ,'flow')");
                    $('#input_cell_flowVo_executorMemory').val(flowVo.executorMemory);
                    $('#input_cell_flowVo_executorMemory').attr("name", "executorMemory");
                    $('#input_cell_flowVo_executorMemory').attr("onclick", "openUpdateCellsProperty(this ,'flow')");
                    $('#input_cell_flowVo_executorNumber').val(flowVo.executorNumber);
                    $('#input_cell_flowVo_executorNumber').attr("name", "executorNumber");
                    $('#input_cell_flowVo_executorNumber').attr("onclick", "openUpdateCellsProperty(this ,'flow')");
                    // ----------------------- cell flow AttributeInfo end   -----------------------
                    $('#cell_flowGroup_property_inc_load_data').show();
                } else {
                    $('#cell_flowGroup_property_inc_no_data').show();
                }
            } else {
                $('#cell_flowGroup_property_inc_load_fail').show();
            }
        }
    });
}

//get Flow list
function getFlowList() {
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window height
    ajaxLoad("", "/page/flow/flow_list_import.html", function (data) {
        // openLayerWindowLoadHtml(data, (window_width / 2), (window_height - 100), "Flows");
        openLayerWindowLoadHtml(data, (window_width / 2), (window_height > 400 ? 620 : 620), "Import Flow");
    });
}

// ClickSlider
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

function updateFlowGroupCellsNameById(selectNodesType) {
    if ('flow' === selectNodesType && $("#input_cell_flowVo_name").val() === $("#span_cell_flowVo_name").text()) {
        isShowUpdateCellsName(false, selectNodesType);
        return;
    }
    if ('flowGroup' === selectNodesType && $("#input_cell_flowGroupVo_name").val() === $("#span_cell_flowGroupVo_name").text()) {
        isShowUpdateCellsName(false, selectNodesType);
        return;
    }
    var requestDataParam = {
        parentId: loadId,
        updateType: selectNodesType
    };
    if ('flow' === selectNodesType) {
        requestDataParam.currentNodeId = $("#input_cell_flowVo_id").val();
        requestDataParam.currentNodePageId = $("#input_cell_flowVo_pageId").val();
        requestDataParam.name = $("#input_cell_flowVo_name").val();
    } else if ('flowGroup' === selectNodesType) {
        requestDataParam.currentNodeId = $("#input_cell_flowGroupVo_id").val();
        requestDataParam.currentNodePageId = $("#input_cell_flowGroupVo_pageId").val();
        requestDataParam.name = $("#input_cell_flowGroupVo_name").val();
    }
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/flowGroup/updateFlowNameById",
        data: requestDataParam,
        async: true,
        traditional: true,
        error: function (request) {
            console.log("attribute update error");
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            // console.log(dataMap);
            if (200 === dataMap.code) {
                //reload xml
                loadXml(dataMap.XmlData);

                selectCellByPageId(requestDataParam.currentNodePageId, false);
                layer.msg("attribute update success", {icon: 1, shade: 0, time: 2000}, function () {
                });
                if ('flow' === selectNodesType) {
                    $("#span_cell_flowVo_name").text(dataMap.nameContent);
                } else if ('flowGroup' === selectNodesType) {
                    $("#span_cell_flowGroupVo_name").text(dataMap.nameContent);
                }
                isShowUpdateCellsName(false, selectNodesType);
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            }
        }
    });
}

//update stops name button
function isShowUpdateCellsName(flag, selectNodesType) {
    if (selectNodesType && 'flow' === selectNodesType) {
        if (flag) {
            $("#input_cell_flowVo_name").val($("#span_cell_flowVo_name").text());
            $("#tr_cell_flowVo_name_info").hide();
            $("#tr_cell_flowVo_name_input").show();
        } else {
            $("#tr_cell_flowVo_name_info").show();
            $("#tr_cell_flowVo_name_input").hide();
        }
    } else if (selectNodesType && 'flowGroup' === selectNodesType) {
        if (flag) {
            $("#input_cell_flowGroupVo_name").val($("#span_cell_flowGroupVo_name").text());
            $("#tr_cell_flowGroupVo_name_info").hide();
            $("#tr_cell_flowGroupVo_name_input").show();
        } else {
            $("#tr_cell_flowGroupVo_name_info").show();
            $("#tr_cell_flowGroupVo_name_input").hide();
        }
    }
}

//Open update cells property
function openUpdateCellsProperty(e, selectNodesType) {
    var updateCellsPropertyTemplateClone = $("#updateCellsPropertyTemplate").clone();
    updateCellsPropertyTemplateClone.find("#cellsValue").attr("id", "cellsPropertyValue");
    updateCellsPropertyTemplateClone.find("#buttonCells").attr("id", "cellsPropertyValueBtn");
    var locked = e.getAttribute('locked');
    if (isExample || 'true' == locked) {
        updateCellsPropertyTemplateClone.find("#cellsPropertyValue").attr("disabled", "disabled");
        updateCellsPropertyTemplateClone.find("#cellsPropertyValueBtn").hide();
    }
    updateCellsPropertyTemplateClone.find("#cellsPropertyValue").css("background-color", "");
    updateCellsPropertyTemplateClone.find("#cellsPropertyValue").attr('name', e.name);
    updateCellsPropertyTemplateClone.find("#cellsPropertyValue").text(e.value);

    if ("flowGroup" === selectNodesType) {
        var flowId = $("#input_cell_flowGroupVo_id").val();
        updateCellsPropertyTemplateClone.find("#cellsPropertyValueBtn").attr("onclick", ("updateFlowGroupAttributes('" + flowId + "','" + e.id + "','cellsPropertyValue',this);"));
    } else {
        var flowGroupId = $("#input_cell_flowVo_id").val();
        updateCellsPropertyTemplateClone.find("#cellsPropertyValueBtn").attr("onclick", ("updateFlowAttributes('" + flowGroupId + "','" + e.id + "','cellsPropertyValue',this)"));
    }
    var p = $(e).offset();
    var openWindowCoordinate = [(p.top + 34) + 'px', (document.body.clientWidth - 300) + 'px'];
    // console.log(openWindowCoordinate);
    layer.open({
        type: 1,
        title: e.name,
        shadeClose: true,
        closeBtn: 0,
        shift: 7,
        anim: 5,//Pop up from top
        shade: 0.1,
        resize: true,//No stretching
        //move: false,//No dragging
        offset: openWindowCoordinate,//coordinate
        area: ['290px', '204px'], //Width Height
        content: updateCellsPropertyTemplateClone.html()
    });
    $("#cellsValue").focus();
    $("#cellsPropertyValue").focus();
}

// Update Flow attributes
function updateFlowAttributes(flowId, propertyId, updateContentId, e) {
    var p = $(e).offset();
    var content = document.getElementById(updateContentId).value;
    if (!content) {
        $("#" + updateContentId + "").css("background-color", "#FFD39B");
        $("#" + updateContentId + "").focus();
        return;
    }
    $('#' + propertyId).val(content);
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/flow/updateFlowBaseInfo",
        data: {
            "id": flowId,
            "description": $('#input_cell_flowVo_description').val(),
            "driverMemory": $('#input_cell_flowVo_driverMemory').val(),
            "executorCores": $('#input_cell_flowVo_executorCores').val(),
            "executorMemory": $('#input_cell_flowVo_executorMemory').val(),
            "executorNumber": $('#input_cell_flowVo_executorNumber').val()

        },
        async: true,
        traditional: true,
        error: function (request) {
            console.log("attribute update error");
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg('success', {
                    icon: 1,
                    shade: 0,
                    time: 2000,
                    offset: ['' + p.top - 30 + 'px', '' + p.left + 50 + 'px']
                }, function () {
                });
                var flowVo = dataMap.flowVo;
                $('#input_cell_flowVo_description').val(flowVo.description)
                $('#input_cell_flowVo_driverMemory').val(flowVo.driverMemory);
                $('#input_cell_flowVo_executorCores').val(flowVo.executorCores);
                $('#input_cell_flowVo_executorMemory').val(flowVo.executorMemory);
                $('#input_cell_flowVo_executorNumber').val(flowVo.executorNumber);
                //baseInfo
                $('#span_cell_flowVo_description').text(flowVo.description);
                $('#span_cell_flowVo_driverMemory').text(flowVo.driverMemory);
                $('#span_cell_flowVo_executorCores').text(flowVo.executorCores);
                $('#span_cell_flowVo_executorMemory').text(flowVo.executorMemory);
                $('#span_cell_flowVo_executorNumber').text(flowVo.executorNumber);
            } else {
                layer.msg('', {icon: 2, shade: 0, time: 2000});
            }
            layer.closeAll('page');
            console.log("attribute update success");
        }
    });
}

// Update FlowGroup attributes
function updateFlowGroupAttributes(flowGroupId, propertyId, updateContentId, e) {
    var p = $(e).offset();
    var content = document.getElementById(updateContentId).value;
    if (!content) {
        $("#" + updateContentId + "").css("background-color", "#FFD39B");
        $("#" + updateContentId + "").focus();
        return;
    }
    $('#' + propertyId).val(content);
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/flowGroup/updateFlowGroupBaseInfo",
        data: {
            "id": flowGroupId,
            "description": $("#input_cell_flowGroupVo_description").val()
        },
        async: true,
        traditional: true,
        error: function (request) {
            console.log("attribute update error");
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg('success', {
                    icon: 1,
                    shade: 0,
                    time: 2000,
                    offset: ['' + p.top - 30 + 'px', '' + p.left + 50 + 'px']
                }, function () {
                });
                var flowGroupVo = dataMap.flowGroupVo;
                $("#input_cell_flowGroupVo_description").val(flowGroupVo.description)
                //baseInfo
                $("#span_cell_flowGroupVo_description").text(flowGroupVo.description);
            } else {
                layer.msg('', {icon: 2, shade: 0, time: 2000});
            }
            layer.closeAll('page');
            console.log("attribute update success");
        }
    });
}

// check flow required
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

//flow Information popup-----
function saveFlow() {
    var currentId = $("#input_node_flow_id").val();
    var currentPageId = $("#input_node_flow_pageId").val();
    if (!currentId && !currentPageId) {
        //alert("Please click the close button and drag it again to create");
        layer.msg('Please click the close button and drag it again to create', {icon: 2, shade: 0, time: 2000});
        return
    }
    var flowName = $("#flowName").val();
    var description = $("#description").val();
    var driverMemory = $("#driverMemory").val();
    var executorNumber = $("#executorNumber").val();
    var executorMemory = $("#executorMemory").val();
    var executorCores = $("#executorCores").val();
    if (!checkFlowInput(flowName, description, driverMemory, executorNumber, executorMemory, executorCores)) {
        // layer.closeAll()
        // alert("flowName Can not be empty")
        layer.msg('flowName Can not be empty', {icon: 2, shade: 0, time: 2000});
        return;
    }
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/flow/updateFlowBaseInfo",
        data: {
            fId: loadId,
            id: currentId,
            pageId: currentPageId,
            name: flowName,
            driverMemory: driverMemory,
            executorCores: executorCores,
            executorMemory: executorMemory,
            executorNumber: executorNumber,
            description: description
        },
        async: true,
        traditional: true,
        error: function (request) {
            console.log("attribute update error");
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                $("#input_node_flow_id").val("");
                $("#input_node_flow_pageId").val("");

                //reload xml
                var xml = mxUtils.parseXml(dataMap.XmlData);
                loadXml(dataMap.XmlData);
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    selectCellByPageId(currentPageId, true);
                    queryFlowOrFlowGroupProperty(currentPageId, loadId);
                    layer.closeAll();
                });
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            }
        }
    });
};

//cancel Flow
function cancelFlow() {
    $("#input_node_flow_id").val("");
    $("#input_node_pageId").val("");
    graphGlobal.removeCells(removeGroupPaths);
    layer.closeAll()
}

// check flowGroup required
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
};

//flowGroup Information popup-----
function saveOrUpdateFlowGroup() {
    var currentId = $("#input_node_flowGroup_id").val();
    var currentPageId = $("#input_node_flowGroup_pageId").val();
    if (!currentId && !currentPageId) {
        //alert("Please click the close button and drag it again to create");
        layer.msg('Please click the close button and drag it again to create', {icon: 2, shade: 0, time: 2000});
        return;
    }
    var flowGroupName = $("#flowGroupName").val();
    var description = $("#flowGroup_description").val();
    if (!checkGroupInput(flowGroupName)) {
        layer.msg('flowName Can not be empty', {icon: 2, shade: 0, time: 2000});
        return;
    } else {
        ajaxRequest({
            cache: true,
            type: "POST",
            url: "/flowGroup/updateFlowGroupBaseInfo",
            data: {
                fId: loadId,
                id: currentId,
                pageId: currentPageId,
                description: description,
                name: flowGroupName
            },
            async: true,
            traditional: true,
            error: function (request) {
                layer.msg('request error ', {icon: 2, shade: 0, time: 2000});
                return;
            },
            success: function (data) {
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    $("#input_node_flowGroup_id").val("");
                    $("#input_node_flowGroup_pageId").val("");

                    //reload xml
                    var xml = mxUtils.parseXml(dataMap.XmlData);
                    loadXml(dataMap.XmlData);
                    layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                        selectCellByPageId(currentPageId, true);
                        queryFlowOrFlowGroupProperty(currentPageId, loadId);
                        layer.closeAll();
                    });
                } else {
                    layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
                }
                //console.log("attribute update success");
            }
        });

    }

}

//cancel Group
function cancelGroup() {
    graphGlobal.removeCells(removeGroupPaths);
    layer.closeAll()
}

// save template
function saveTemplateFun() {
    var getXml = thisEditor.getGraphXml();
    var xml_outer_html = getXml.outerHTML;
    layer.prompt({
        title: 'please enter the template name',
        formType: 0,
        btn: ['submit', 'cancel']
    }, function (text, index) {
        layer.close(index);
        ajaxRequest({
            cache: true,//Keep cached data
            type: "POST",//Request type post
            url: "/flowTemplate/saveFlowTemplate",
            data: {
                value: xml_outer_html,
                load: loadId,
                name: text,
                templateType: "GROUP"
            },
            async: true,
            error: function (request) {//Operation after request failure
                console.log(" save template error");
                return;
            },
            success: function (data) {//After the request is successful
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

// upload template
function uploadFlowGroupTemplateBtn() {
    document.getElementById("flowTemplateFile").click();
}

// upload template
function uploadTemplateFile(element) {
    if (!FileTypeCheck(element)) {
        return false;
    }
    if (url) {
        return false;
    }
    var formData = new FormData($('#uploadForm')[0]);
    ajaxRequest({
        type: 'post',
        url: '/flowTemplate/uploadXmlFile',
        data: formData,
        cache: false,
        processData: false,
        contentType: false,
    }).success(function (data) {
        var dataMap = JSON.parse(data);
        if (200 === dataMap.code) {
            layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
            });
        } else {
            layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
        }
    }).error(function () {
        layer.msg("Upload failure", {icon: 2, shade: 0, time: 2000});
    });
}

// check file type
function FileTypeCheck(element) {
    if (element.value == null || element.value == '') {
        layer.msg('please upload the XML file', {icon: 2, shade: 0, time: 2000});
        this.focus()
        return false;
    }
    var length = element.value.length;
    var charindex = element.value.lastIndexOf(".");
    var ExtentName = element.value.substring(charindex, charindex + 4);
    if (!(ExtentName == ".xml")) {
        layer.msg('please upload the XML file', {icon: 2, shade: 0, time: 2000});
        this.focus()
        return false;
    }
    return true;
}

function loadingXml(id, loadId) {
    var loadType = Format.customizeType;
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        type: 'post',
        data: {
            templateId: id,
            loadType: loadType,
            load: loadId
        },
        async: true,
        url: "/flowTemplate/loadingXmlPage",
        success: function (data) {
            var dataMap = JSON.parse(data);
            var icon_code = 2;
            if (200 === dataMap.code) {
                icon_code = 1;
                layer.msg(dataMap.errorMsg, {icon: icon_code, shade: 0.7, time: 2000}, function () {
                    window.location.reload();
                });
            } else {
                layer.msg(dataMap.errorMsg, {icon: icon_code, shade: 0.7, time: 2000}, function () {

                });
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        },
        error: function (data) {
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    })
}

// open template list
function openTemplateList() {
    if (isExample) {
        layer.msg('This is an example, you can\'t edit', {icon: 2, shade: 0, time: 2000});
        return;
    }
    var url = "";
    var functionNameStr = "";
    if ('TASK' !== Format.customizeType && 'GROUP' !== Format.customizeType) {
        return;
    }
    ajaxRequest({
        url: "/flowTemplate/flowTemplateList",
        type: "post",
        async: false,
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var temPlateList = dataMap.temPlateList;
                var showSelectDivHtml = '<div style="width: 100%;height: 146px;position: relative;">';
                var showOptionHtml = '';
                for (var i = 0; i < temPlateList.length; i++) {
                    showOptionHtml += ("<option value=" + temPlateList[i].id + " >" + temPlateList[i].name + "</option>");
                }
                var showSelectHtml = 'There is no template, please create';
                var loadTemplateBtn = '';
                if (showOptionHtml) {
                    showSelectHtml = ('<div style="width: 100%;text-align: center;">'
                        + '<select name="loadingXmlSelect" id="loadingXmlSelectNew" style="width: 80%;margin-top: 15px;">'
                        + '<option value=\'-1\' >------------please choose------------</option>'
                        + showOptionHtml
                        + '</select>'
                        + '</div>');
                    loadTemplateBtn = '<div style="position: absolute;bottom: 12px;right: 10px;">'
                        + '<input type="button" class="btn" value="Submit" onclick="loadTemplateFun()"/>'
                        + '</div>';
                }
                showSelectDivHtml += (showSelectHtml + loadTemplateBtn + '</div>');
                layer.open({
                    type: 1,
                    title: '<span style="color: #269252;">Please choose</span>',
                    shadeClose: false,
                    resize: false,
                    closeBtn: 1,
                    shift: 7,
                    area: ['500px', '200px'], //Width height
                    skin: 'layui-layer-rim', //Add borders
                    content: showSelectDivHtml
                });
            } else {
                layer.msg("No template, please create", {time: 2000});
            }
        }
    });
}

// load template
function loadTemplateFun() {
    var id = $("#loadingXmlSelectNew").val();
    if (id == '-1') {
        layer.msg('Please choose template', {icon: 2, shade: 0, time: 2000});
        return;
    }

    var name = $("#loadingXmlSelect option:selected").text();
    layer.open({
        title: 'LoadTemplate',
        content: 'Are you sure you want to load ' + name + '？',
        btn: ['submit', 'cancel'],
        yes: function (index, layero) {
            loadingXml(id, loadId);
            var oDiv = document.getElementById("divloadingXml");
            oDiv.style.display = "none";
        },
        btn2: function (index, layero) {
            var oDiv = document.getElementById("divloadingXml");
            oDiv.style.display = "none";
        }, cancel: function () {
            var oDiv = document.getElementById("divloadingXml");
            oDiv.style.display = "none";
        }
    });
}

// run cells
function RunFlowOrFlowGroupCells(includeEdges) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    var cells = graphGlobal.getSelectionCells();
    if (cells != null && cells.length > 1) {
        layer.msg('Multiple runs cannot be selected at the same time', {icon: 2, shade: 0, time: 2000});
        return;
    }
    ajaxRequest({
        type: "post",//Request type post
        url: "/mxGraph/groupRightRun",
        data: {pId: loadId, nodeId: cells[0].id},
        async: true,//Synchronous Asynchronous
        error: function (request) {//Operation after request failure
            layer.msg("Startup failure：" + dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            return;
        },
        success: function (data) {//After the request is successful
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    //Jump to the monitor page after starting successfully
                    if (dataMap.processGroupId) {
                        new_window_open("/page/processGroup/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS_GROUP&load=" + dataMap.processGroupId);
                    } else if (dataMap.processId) {
                        new_window_open("/page/process/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS&load=" + dataMap.processId);
                    }
                });
            } else {
                layer.msg("Startup failure：" + dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            }
        }
    })
}

//run flowGroup
function runFlowGroup(runMode) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    var data = {flowGroupId: loadId}
    if (runMode) {
        data.runMode = runMode;
    }
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flowGroup/runFlowGroup",
        //data:$('#loginForm').serialize(),//Serialize the form
        data: data,
        async: true,//Synchronous Asynchronous
        error: function (request) {//Operation after request failure
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000}, function () {
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            });

            return;
        },
        success: function (data) {//After the request is successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    //Jump to the monitoring page after starting successfully
                    new_window_open("/page/processGroup/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS_GROUP&load=" + dataMap.processGroupId, '_blank');
                });
            } else {
                layer.msg("Startup failure：" + dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

//toast error msg
function toastErrorMsg(errorMsg) {
    switch (errorMsg) {
        case 'loop':
            layer.msg('不允许连接相同元素！', {icon: 2, shade: 0, time: 2000});
            break;
        case 'muti':
            layer.msg('不允许同时连接两条线！', {icon: 2, shade: 0, time: 2000});
            break;
        case 'disConnect':
            layer.msg('不允许单独移动边！', {icon: 2, shade: 0, time: 2000});
            break;
    }
}
