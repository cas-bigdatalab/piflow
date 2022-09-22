// Extends EditorUi to update I/O action states based on availability of backend

var parentsId, xmlDate, maxStopPageId, isExample, consumedFlag, timerPath, statusgroup, removegroupPaths, stopsId;

var index = true;
var flag = 0;
var pathsCells = [];
var thisEditor = null;
var graphGlobal = null;

//init data
function initFlowDrawingBoardData(loadId, parentAccessPath) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        type: "get",
        url: "/flow/drawingBoardData",
        async: false,
        data: {
            load: loadId,
            parentAccessPath: parentAccessPath
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                window.parent.postMessage(false);
                if (dataMap.parentsId) {
                    parentsId = dataMap.parentsId;
                } else {
                    parentsId = 'null';
                }
                let herf = top.window.location.href.split("src=")[1];
                if (herf.indexOf('BreadcrumbSchedule') !== -1) {
                    top.document.getElementById('BreadcrumbSchedule').style.display = 'block';
                    top.document.getElementById('BreadcrumbFlow').style.display = 'none';
                } else {
                    top.document.getElementById('BreadcrumbFlow').style.display = 'block';
                    top.document.getElementById('BreadcrumbSchedule').style.display = 'none';
                }
                top.document.getElementById('BreadcrumbGroup').style.display = 'none';
                top.document.getElementById('BreadcrumbProcess').style.display = 'none';
                top.document.getElementById('BreadcrumbProcessGroup').style.display = 'none';

                var link = top.document.getElementById('FlowParents');
                if (parentsId !== 'null') {
                    link.style.display = 'inline-block';
                    link.href = '#/drawingBoard?src=/drawingBoard/page/flowGroup/mxGraph/index.html?drawingBoardType=GROUP&parentAccessPath=flowGroupList&load=' + parentsId;
                } else {
                    link.style.display = 'none';
                }

                // for (var key in window.parent.__VUE_HOT_MAP__){
                //     if( window.parent.__VUE_HOT_MAP__[key].options.name === 'DrawingBoard'){
                //         window.parent.postMessage({
                //             parentsId :parentsId
                //         },'*');
                //     }
                // }
                xmlDate = dataMap.xmlDate;
                maxStopPageId = dataMap.maxStopPageId;
                isExample = dataMap.isExample;
                if (dataMap.groupsVoList) {
                    if (dataMap.groupsVoList && dataMap.groupsVoList.length > 0) {
                        for (var i = 0; i < dataMap.groupsVoList.length; i++) {
                            var groupsVoList_i = dataMap.groupsVoList[i];
                            if (groupsVoList_i && '' !== groupsVoList_i) {
                                Sidebar.prototype.component_Stop_data.push({
                                    component_name: groupsVoList_i.groupName,
                                    component_group: groupsVoList_i.stopsTemplateVoList,
                                    component_prefix: (web_header_prefix + "/images/"),
                                    addImagePaletteId: 'clipart'
                                });
                            }
                        }
                    }
                }
                if (dataMap.dataSourceVoList) {
                    if (dataMap.dataSourceVoList && dataMap.dataSourceVoList.length > 0) {
                        Sidebar.prototype.component_DataSource_data.push({
                            component_name: 'DataSource',
                            component_group: dataMap.dataSourceVoList,
                            component_prefix: (web_header_prefix + "/images/"),
                            addImagePaletteId: 'clipart'
                        });
                    }
                }
            } else {
                window.parent.postMessage(false);
                window_location_href("/page/error/errorPage.html");
            }
            // $('#fullScreen').hide();
            // window.parent.postMessage(false);
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
        data: {imageType: "TASK"},
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
                this.data = {imageType: "TASK"};
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

//init mxGraph
function initFlowGraph() {
    Actions.prototype.RunAll = runFlow;
    EditorUi.prototype.saveGraphData = saveXml;
    EditorUi.prototype.customUpdeteImg = updateMxGraphCellImage;
    Menus.prototype.customRightMenu = ['runAll'];
    Menus.prototype.customCellRightMenu = ['runCurrentStop', 'runCurrentAndBelowStops'];
    Actions.prototype.RunCells = RunFlowOrFlowCells;
    Actions.prototype.RunCellsUp = RunFlowOrFlowCellsUp;
    Graph.prototype.errorToast = toastErrorMsg;
    Format.hideSidebar(false, true);
    //EditorUi.prototype.formatWidth = 0;
    $("#right-group-wrap")[0].style.display = "block";
    var editorUiInit = EditorUi.prototype.init;
    EditorUi.prototype.init = function () {
        editorUiInit.apply(this, arguments);
        graphGlobal = this.editor.graph;
        undoManagerGlobal = this.editor.undoManager;
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
            flowMxEventClickFunc(evt.properties.cell, consumedFlag);
        });
        loadXml(xmlDate);
        // change size
        graphGlobal.setCellsResizable(false);
        // repeat connection
        graphGlobal.setMultigraph(false);
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

//open xml file
function openXml() {
    ajaxRequest({
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/flow/loadData",
        //data:$('#loginForm').serialize(),//Serialize the form
        async: true,//Synchronous Asynchronous
        error: function (request) {//Operation after request failure
            return;
        },
        success: function (data) {//After the request is successful
            loadXml(data);
            console.log("success");
        }
    });
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

//Erase drawing board records
function eraseRecord() {
    thisEditor.lastSnapshot = new Date().getTime();
    thisEditor.undoManager.clear();
    thisEditor.ignoredChanges = 0;
    thisEditor.setModified(false);
}

//mxGraph click event
function flowMxEventClickFunc(cell, consumedFlag) {
    $("#flow_info_inc_id").hide();
    $("#flow_path_inc_id").hide();
    $("#flow_property_inc_id").hide();
    if (index) {
        $(".right-group").toggleClass("open-right");
        $(".ExpandSidebar").toggleClass("ExpandSidebar-open");
        $(".triggerSlider i").removeClass("fa fa-angle-left fa-2x ").toggleClass("fa fa-angle-right fa-2x");
        index = false
    }
    // console.log(cell);
    if (!consumedFlag) {
        $("#flow_info_inc_id").show();
        // info
        queryFlowInfo(loadId);
        return;
    }
    var cells_arr = graphGlobal.getSelectionCells();
    if (cells_arr.length !== 1) {
        $("#flow_info_inc_id").show();
        // info
        queryFlowInfo(loadId);
    } else {
        var selectedCell = cells_arr[0]
        if (selectedCell && (selectedCell.edge === 1 || selectedCell.edge)) {
            $("#flow_path_inc_id").show();
            queryPathInfo(selectedCell.id, loadId)
        } else if (selectedCell && selectedCell.style && (selectedCell.style).indexOf("image\;") === 0) {
            $("#flow_property_inc_id").show();
            queryStopsProperty(selectedCell.id, loadId);
        } else if (selectedCell && selectedCell.style && (selectedCell.style).indexOf("text\;") === 0) {
            $("#flow_info_inc_id").show();
            // info
            queryFlowInfo(loadId);
        }
    }
}

//query Flow info
function queryFlowInfo(loadId) {
    $("#flow_path_inc_id").hide();
    $("#flow_property_inc_id").hide();
    $("#runningProcessID").hide();
    $("#flow_info_inc_id").show();
    ajaxRequest({
        type: "POST",
        url: "/flow/queryFlowData",
        async: true,
        data: {"load": loadId},
        success: function (data) {//After the request is successful
            var dataMap = JSON.parse(data);
            $('#flow_info_inc_loading').hide();
            if (200 === dataMap.code) {
                var flowVo = dataMap.flow;
                if (flowVo) {
                    $("#span_flowVo_id").text(flowVo.id);
                    $("#span_flowVo_name").text(flowVo.name);
                    $("#span_flowVo_description").text(flowVo.description);
                    $("#span_flowVo_crtDttmStr").text(flowVo.crtDttmString);
                    $("#span_flowVo_stopsCounts").text(flowVo.stopQuantity);
                    $('#flow_info_inc_load_data').show();
                } else {
                    $('#flow_info_inc_no_data').show();
                }
                var runningProcessVoList = dataMap.runningProcessVoList;
                if (runningProcessVoList) {
                    $("#runningProcessID").show();
                    var runningProcessID_tbody = $("#runningProcessID").find("tbody");
                    if (runningProcessID_tbody) {
                        var tableTitle = '<tr>'
                            + '<td style="width: 50%;"><label>processName</label></td>'
                            + '<td style="width: 50%;"><label>startTime</label></td>'
                            + '</tr>';
                        var tableAllTd = '';
                        for (var i = 0; i < runningProcessVoList.length; i++) {
                            tableAllTd += ('<tr>'
                                + '<td style="border: 1px solid #e8e8e8; width: 50%;">'
                                + '<a href="' + web_base_origin + web_drawingBoard + '/page/process/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS&load=' + runningProcessVoList[i].id + '">' + runningProcessVoList[i].name + '</a>'
                                + '</td>'
                                + '<td style="border: 1px solid #e8e8e8; width: 50%;"><span>' + runningProcessVoList[i].startTime + '</span></td>'
                                + '</tr>');
                        }
                        runningProcessID_tbody.html(tableTitle + tableAllTd);
                    }
                }
            } else {
                $('#flow_info_inc_load_fail').show();
            }
        },
        error: function (request) {//Operation after request failure
            $('#flow_info_inc_loading').hide();
            $('#flow_info_inc_load_fail').show();
            alert("Request Failed");
            return;
        }
    });
}

//query Flow path
function queryPathInfo(stopPageId, loadId) {
    ajaxRequest({
        type: "POST",
        url: "/path/queryPathInfo",
        async: true,
        data: {"id": stopPageId, "fid": loadId},
        success: function (data) {
            var dataMap = JSON.parse(data);
            $('#flow_path_inc_loading').hide();
            if (200 === dataMap.code) {
                var queryInfo = dataMap.queryInfo;
                if (queryInfo) {
                    $('#flow_path_inc_load_data').show();
                    // Flow Path Information
                    $("#span_flowPathVo_pageId").text(queryInfo.pageId);
                    $("#span_flowPathVo_inport").text(queryInfo.inport);
                    $("#span_flowPathVo_outport").text(queryInfo.outport);
                    $("#span_flowPathVo_from").text(queryInfo.from);
                    $("#span_flowPathVo_to").text(queryInfo.to);
                    var flowVo = queryInfo.flowVo
                    if (flowVo) {
                        $("#span_flowPathVo_flowName").text(flowVo.name);
                    }
                } else {
                    $('#flow_path_inc_no_data').show();
                }
            } else {
                queryFlowInfo(loadId);
                console.log("Path attribute query null");
            }
        },
        error: function (request) {
            //alert("Jquery Ajax request error!!!");
            return;
        }
    });
}

//query Stops info and property
function queryStopsProperty(stopPageId, loadId) {
    $("#div_datasource_html").hide();
    $("#div_propertiesVo_html").hide();
    $("#div_customized_html").hide();
    $("#div_stops_checkpoint_html").hide();
    $("#div_del_last_reload").hide();
    $("#div_properties_example_html").hide();
    isShowUpdateStopsName(false);
    ajaxRequest({
        type: "POST",
        url: "/stops/queryIdInfo",
        async: true,
        data: {"stopPageId": stopPageId, "fid": loadId},
        success: function (data) {
            var dataMap = JSON.parse(data);
            $('#process_property_inc_loading').hide();
            if (200 === dataMap.code) {
                var stopsVoData = dataMap.stopsVo;
                stopsId = stopsVoData.id;
                if (stopsVoData) {
                    //Remove the timer if successful
                    window.clearTimeout(timerPath);

                    // ----------------------- baseInfo start -----------------------
                    $('#input_flowStopsVo_id').val(stopsVoData.id);
                    $('#input_flowStopsVo_pageId').val(stopsVoData.pageId);
                    $('#span_stopsVo_name').text(stopsVoData.name);
                    $('#span_processStopVo_description').text(stopsVoData.description);
                    $('#span_processStopVo_groups').text(stopsVoData.groups);
                    $('#span_flowStopsVo_bundle').text(stopsVoData.bundel);
                    $('#span_flowStopsVo_version').text(stopsVoData.version);
                    $('#span_processStopVo_owner').text(stopsVoData.owner);
                    $('#span_processStopVo_crtDttmString').text(stopsVoData.crtDttmString);
                    if (isExample) {
                        $('#btn_show_update').hide();
                    }
                    // ----------------------- baseInfo end   -----------------------

                    // ----------------------- AttributeInfo start -----------------------
                    $("#div_properties_example_table").html("");
                    var tbody_example = document.createElement("tbody");
                    // propertiesVo
                    var propertiesVo = stopsVoData.propertiesVo;
                    if (propertiesVo && propertiesVo.length > 0) {
                        var tbody = document.createElement("tbody");
                        for (var y = 0; y < propertiesVo.length; y++) {
                            if (!propertiesVo[y]) {
                                continue;
                            }
                            var propertyVo = propertiesVo[y];
                            var propertyVo_id = propertyVo.id;
                            var propertyVo_name = propertyVo.name;
                            var propertyVo_description = propertyVo.description;
                            var propertyVo_displayName = propertyVo.displayName;
                            var propertyVo_customValue = (!propertyVo.customValue || customValue == 'null') ? '' : propertyVo.customValue;
                            var propertyVo_allowableValues = propertyVo.allowableValues;
                            var propertyVo_isSelect = propertyVo.isSelect;
                            var propertyVo_required = propertyVo.required;
                            var propertyVo_sensitive = propertyVo.sensitive;
                            var propertyVo_isLocked = propertyVo.isLocked;
                            var propertyVo_example = propertyVo.example;

                            // create tr and td
                            var tr_i = document.createElement("tr");
                            tr_i.setAttribute('class', 'trTableStop');
                            var td_0 = document.createElement("td");
                            var td_1 = document.createElement("td");
                            var td_2 = document.createElement("td");
                            var td_3 = document.createElement("td");

                            // property name
                            var spanDisplayName = document.createElement('span');
                            spanDisplayName.textContent = propertyVo_name;
                            // property description
                            var img = document.createElement("img");
                            img.setAttribute('src', web_drawingBoard + '/img/descIcon.png');
                            img.style.cursor = "pointer";
                            img.setAttribute('title', '' + propertyVo_description + '');
                            // property value
                            var property_value_obj;
                            //If it is greater than 4 and isSelect is true, there is a drop-down box
                            if (propertyVo_allowableValues.length > 4 && propertyVo_isSelect) {
                                propertyVo_allowableValues = propertyVo_allowableValues;
                                var selectValue = JSON.parse(propertyVo_allowableValues);
                                var selectInfo = JSON.stringify(selectValue);
                                var strs = selectInfo.split(",");

                                property_value_obj = document.createElement('select');
                                property_value_obj.style.height = "32px";
                                property_value_obj.setAttribute('id', '' + propertyVo_name + '');
                                property_value_obj.setAttribute('onChange', "updateStopsProperty('" + propertyVo_id + "','" + propertyVo_name + "','select')");
                                property_value_obj.setAttribute('class', 'form-control');
                                var optionDefault = document.createElement("option");
                                optionDefault.value = '';
                                optionDefault.innerHTML = '';
                                optionDefault.setAttribute('selected', 'selected');
                                property_value_obj.appendChild(optionDefault);
                                //Loop to assign value to select
                                for (i = 0; i < strs.length; i++) {
                                    var option = document.createElement("option");
                                    option.style.backgroundColor = "#DBDBDB";
                                    var option_value = strs[i].replace("\"", "").replace("\"", "").replace("\[", "").replace("\]", "");
                                    option.value = option_value;
                                    option.innerHTML = option_value;
                                    //Sets the default selection
                                    if (strs[i].indexOf('' + propertyVo_customValue + '') != -1) {
                                        option.setAttribute('selected', 'selected');
                                    }
                                    property_value_obj.appendChild(option);
                                }
                            } else {
                                property_value_obj = document.createElement('input');
                                property_value_obj.setAttribute('class', 'form-control');
                                property_value_obj.setAttribute('id', '' + propertyVo_id + '');
                                property_value_obj.setAttribute('name', '' + propertyVo_name + '');
                                property_value_obj.setAttribute('onclick', 'openUpdateStopsProperty(this,false,'+ JSON.stringify(propertyVo.language) +','+propertyVo.isLocked+' )');
                                property_value_obj.setAttribute('locked', propertyVo_isLocked);
                                property_value_obj.setAttribute('data', propertyVo_customValue);
                                property_value_obj.setAttribute('readonly', 'readonly');
                                property_value_obj.style.cursor = "pointer";
                                property_value_obj.style.background = "rgb(245, 245, 245)";
                                property_value_obj.setAttribute('value', '' + propertyVo_customValue + '');
                                //Port uneditable
                                if (propertyVo_sensitive){
                                    property_value_obj.setAttribute('type', 'password');
                                }
                                if ("outports" == propertyVo_name || "inports" == propertyVo_name) {
                                    property_value_obj.setAttribute('disabled', 'disabled');
                                }
                                if (propertyVo_required) {
                                    property_value_obj.setAttribute('data-toggle', 'true');
                                }
                                $("#div_datasource_html").show();
                            }
                            // Is required
                            var spanFlag = document.createElement('span');
                            if (propertyVo_required) {
                                spanFlag.setAttribute('style', 'color:red');
                                spanFlag.textContent = '*';
                            }

                            // set td style
                            td_0.style.width = "60px";
                            td_1.style.width = "25px";

                            // append td content
                            td_0.appendChild(spanDisplayName);
                            td_1.appendChild(img);
                            td_2.appendChild(property_value_obj);
                            td_3.appendChild(spanFlag);

                            // append tr content
                            tr_i.appendChild(td_0);
                            tr_i.appendChild(td_1);
                            tr_i.appendChild(td_2);
                            tr_i.appendChild(td_3);
                            tbody.appendChild(tr_i);

                            if (propertyVo_example) {
                                var tbody_example_tr_i = document.createElement("tr");
                                var tbody_example_td_0 = document.createElement("td");
                                var tbody_example_td_1 = document.createElement("td");
                                var tbody_example_td_2 = document.createElement("td");
                                var tbody_example_td_2_obj = document.createElement('input');
                                tbody_example_td_0.innerHTML = td_0.outerHTML;
                                tbody_example_td_1.innerHTML = td_1.outerHTML;
                                tbody_example_td_0.style.width = "60px";
                                tbody_example_td_1.style.width = "25px";
                                tbody_example_td_2_obj.setAttribute('class', 'form-control');
                                tbody_example_td_2_obj.setAttribute('value', '' + propertyVo_example + '');
                                tbody_example_td_2_obj.setAttribute('readonly', 'readonly');
                                tbody_example_td_2.appendChild(tbody_example_td_2_obj);
                                tbody_example_tr_i.appendChild(tbody_example_td_0);
                                tbody_example_tr_i.appendChild(tbody_example_td_1);
                                tbody_example_tr_i.appendChild(tbody_example_td_2);
                                tbody_example.appendChild(tbody_example_tr_i);
                                if (propertyVo_sensitive){
                                    tbody_example_td_2_obj.setAttribute('type', 'password');
                                }
                            }
                        }
                        if (isExample) {
                            $('#datasourceSelectElement').attr('disabled', 'disabled');
                        }
                        $("#div_propertiesVo_table").html(tbody);
                        $("#div_propertiesVo_html").show();
                        if (tbody_example.innerHTML) {
                            $("#div_properties_example_table").html(tbody_example);
                            $("#div_properties_example_html").show();
                        }
                    }


                    //checkboxCheckpoint
                    var checkboxCheckpoint = document.createElement('input');
                    checkboxCheckpoint.setAttribute('type', 'checkbox');
                    checkboxCheckpoint.setAttribute('id', 'isCheckpoint');
                    if (stopsVoData.isCheckpoint) {
                        checkboxCheckpoint.setAttribute('checked', 'checked');
                    }
                    if (isExample) {
                        checkboxCheckpoint.setAttribute('disabled', 'disabled');
                    }
                    checkboxCheckpoint.setAttribute('onclick', 'saveCheckpoints("' + stopsVoData.id + '")');
                    $("#div_stops_checkpoint_html").html("");
                    $("#div_stops_checkpoint_html").append(checkboxCheckpoint);
                    $("#div_stops_checkpoint_html").append('<span>&nbsp;&nbsp;Whether to add Checkpoint</span>');
                    $('#div_stops_checkpoint_html').show();

                    //stopsCustomizedPropertyVoList
                    if (stopsVoData.isCustomized) {
                        $("#div_a_customized_html").attr("href", "javascript:openAddStopCustomAttrPage('" + stopsVoData.id + "');");
                        $("#div_table_customized_html").html("");
                        var tr_default = document.createElement('tr');
                        var th_0_default = document.createElement('th');
                        var th_1_default = document.createElement('th');
                        tr_default.setAttribute("style", "border: 1px solid #e2e2e2;");
                        th_0_default.setAttribute("colspan", 2);
                        th_0_default.setAttribute("style", "border-bottom: 1px solid #e2e2e2; width: 85px;text-align: center;");
                        th_1_default.setAttribute("colspan", 2);
                        th_1_default.setAttribute("style", "border-bottom: 1px solid #e2e2e2;");
                        tr_default.appendChild(th_0_default);
                        tr_default.appendChild(th_1_default);
                        $("#div_table_customized_html").append(tr_default);
                        var tr_i = "";
                        if (stopsVoData.stopsCustomizedPropertyVoList && stopsVoData.stopsCustomizedPropertyVoList.length > 0) {
                            var stopsCustomizedPropertyVoList = stopsVoData.stopsCustomizedPropertyVoList;
                            for (var i = 0; i < stopsCustomizedPropertyVoList.length; i++) {
                                tr_i = setCustomizedTableHtml(stopsVoData.pageId, stopsCustomizedPropertyVoList[i], stopsVoData.outPortType);
                                $("#div_table_customized_html").append(tr_i);
                            }
                        }
                        $("#div_customized_html").show();
                    }
                    // datasource
                    getDatasourceList(stopsVoData.id, stopsVoData.pageId, stopsVoData.dataSourceVo);

                    var oldPropertiesVo = stopsVoData.oldPropertiesVo;
                    if (oldPropertiesVo && oldPropertiesVo.length > 0) {
                        var table = document.createElement("table");
                        table.style.borderCollapse = "separate";
                        table.style.borderSpacing = "0px 5px";
                        table.style.marginLeft = "12px";
                        table.style.width = "97%";
                        var tbody = document.createElement("tbody");
                        for (var y = 0; y < oldPropertiesVo.length; y++) {
                            var select = document.createElement('select');
                            //select.style.width = "290px";
                            select.style.height = "32px";
                            select.setAttribute('id', 'old_' + oldPropertiesVo[y].name + '');
                            select.setAttribute('class', 'form-control');
                            select.setAttribute('disabled', 'disabled');
                            var displayName = oldPropertiesVo[y].displayName;
                            var customValue = oldPropertiesVo[y].customValue;
                            var allowableValues = oldPropertiesVo[y].allowableValues;
                            var isSelect = oldPropertiesVo[y].isSelect;
                            //Is it required?
                            var required = oldPropertiesVo[y].required;
                            //If it is greater than 4 and isSelect is true, there is a drop-down box
                            if (allowableValues.length > 4 && isSelect) {
                                var selectValue = JSON.parse(allowableValues);
                                var selectInfo = JSON.stringify(selectValue);
                                var strs = selectInfo.split(",");
                                var optionDefault = document.createElement("option");
                                optionDefault.value = '';
                                optionDefault.innerHTML = '';
                                optionDefault.setAttribute('selected', 'selected');
                                select.appendChild(optionDefault);
                                //Loop to assign value to select
                                for (i = 0; i < strs.length; i++) {
                                    var option = document.createElement("option");
                                    option.style.backgroundColor = "#DBDBDB";
                                    option.value = strs[i].replace("\"", "").replace("\"", "").replace("\[", "").replace("\]", "");
                                    option.innerHTML = strs[i].replace("\"", "").replace("\"", "").replace("\[", "").replace("\]", "");
                                    //Sets the default selection
                                    if (strs[i].indexOf('' + customValue + '') != -1) {
                                        option.setAttribute('selected', 'selected');
                                    }
                                    select.appendChild(option);
                                }
                            }
                            var displayName = document.createElement('input');
                            if (required)
                                displayName.setAttribute('data-toggle', 'true');
                            displayName.setAttribute('class', 'form-control');
                            displayName.setAttribute('id', 'old_' + oldPropertiesVo[y].id + '');
                            displayName.setAttribute('name', '' + oldPropertiesVo[y].name + '');
                            displayName.setAttribute('locked', oldPropertiesVo[y].isLocked);
                            // displayName.style.width = "290px";
                            displayName.setAttribute('readonly', 'readonly');
                            displayName.style.cursor = "pointer";
                            displayName.style.background = "rgb(245, 245, 245)";
                            customValue = customValue == 'null' ? '' : customValue;
                            displayName.setAttribute('value', '' + customValue + '');
                            var spanDisplayName = 'span' + oldPropertiesVo[y].displayName;
                            var spanDisplayName = document.createElement('span');
                            var spanFlag = document.createElement('span');
                            spanFlag.setAttribute('style', 'color:red');
                            mxUtils.write(spanDisplayName, '' + oldPropertiesVo[y].name + '' + ": ");
                            mxUtils.write(spanFlag, '*');
                            //Port uneditable
                            if ("outports" == oldPropertiesVo[y].displayName || "inports" == oldPropertiesVo[y].displayName) {
                                displayName.setAttribute('disabled', 'disabled');
                            }

                            var img = document.createElement("img");
                            img.setAttribute('src', web_drawingBoard + '/img/descIcon.png');
                            img.style.cursor = "pointer";
                            img.setAttribute('title', '' + oldPropertiesVo[y].description + '');
                            var tr = document.createElement("tr");
                            tr.setAttribute('class', 'trTableStop');
                            var td = document.createElement("td");
                            td.style.width = "60px";
                            var td1 = document.createElement("td");
                            var td2 = document.createElement("td");
                            var td3 = document.createElement("td");
                            td3.style.width = "25px";
                            //Appendchild () appends elements
                            td.appendChild(spanDisplayName);
                            td3.appendChild(img);
                            //This loop is greater than 4 append drop-down, less than 4 default text box
                            if (allowableValues.length > 4 && isSelect) {
                                td1.appendChild(select);
                            } else {
                                td1.appendChild(displayName);
                                if (required) {
                                    td2.appendChild(spanFlag);
                                }
                            }
                            tr.appendChild(td);
                            tr.appendChild(td3);
                            tr.appendChild(td1);
                            tr.appendChild(td2);
                            tbody.appendChild(tr);
                            table.appendChild(tbody);
                        }
                        var old_data_div = '<div id="del_last_reload_div" style="line-height: 27px;margin-left: 10px;font-size: 20px;">'
                            + '<span>last reload data</span>'
                            + '<button class="btn" style="margin-left: 2px;" onclick="deleteLastReloadData(\'' + stopsVoData.id + '\')"><i class="icon-trash"></i></button>'
                            + '</div>';
                        table.setAttribute('id', 'del_last_reload_table');
                        var attributeInfoDivObj = $("#isCheckpoint").parent();
                        attributeInfoDivObj.append(old_data_div);
                        attributeInfoDivObj.append(table);
                        attributeInfoDivObj.append("<hr>");
                    }
                    // ----------------------- AttributeInfo end   -----------------------

                    $('#process_property_inc_load_data').show();
                } else {
                    $('#process_property_inc_no_data').show();
                }
            } else {
                //STOP attribute query null
                if (!timerPath) {
                    timerPath = window.setTimeout(queryStopsProperty(stopPageId, loadId), 500);
                }
                flag++;
                if (flag > 5) {
                    window.clearTimeout(timerPath);
                    return;
                }
            }
            layer.close(layer.index);
        },
        error: function (request) {
            //alert("Jquery Ajax request error!!!");
            return;
        }
    });
}

//open Datasource list
function openDatasourceList() {
    var window_width = $(window).width();//Get browser window width
    var window_height = $(window).height();//Get browser window height
    // openLayerTypeIframeWindowLoadUrl("/page/datasource/data_source_list.html",(window_width - 100),(window_height - 100),DatasourceList)
    // openLayerTypeIframeWindowLoadUrl("/page/datasource/data_source_list.html", (window_width - 100), (window_height - 100),'Data Source')

    ajaxLoad("", "/page/dataSource/data_source_list.html", function (data) {
        var open_window_width = (window_width > 300 ? 1200 : window_width);
        var open_window_height = (window_height > 400 ? 570 : window_height);
        openLayerWindowLoadHtml(data,open_window_width,open_window_height,"Data Source");
        // $("#debug_app_id").html(appId);
        // $("#debug_stop_name").html(stopName);
        // $("#debug_port_name").html(portName);
        // changePageNo(1);
    });


}

//query datasource list
function getDatasourceList(stop_id, stops_page_id, dataSourceVo) {
    ajaxRequest({
        type: "POST",
        url: "/datasource/getDatasourceList",
        async: true,
        data: {},
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var dataSourceList = dataMap.data;
                var select_html = '<select id="datasourceSelectElement" class="form-control" style="width: 100%;" onchange="fillDatasource(this,\'' + stop_id + '\',\'' + stops_page_id + '\')">'
                if (dataSourceList && dataSourceList.length > 0) {
                    var option_html = '<option value="">please select datasource...</option>';
                    var dataSourceVoId = '';
                    if (dataSourceVo && dataSourceVo.id) {
                        dataSourceVoId = dataSourceVo.id;
                    }
                    if ('' === dataSourceVoId) {
                        option_html = '<option selected="selected" value="">please select datasource...</option>';
                    }
                    for (var i = 0; i < dataSourceList.length; i++) {
                        if (dataSourceList[i].id === dataSourceVoId) {
                            option_html += ('<option selected="selected" value="' + dataSourceList[i].id + '">');
                        } else {
                            option_html += ('<option value="' + dataSourceList[i].id + '">');
                        }
                        option_html += (dataSourceList[i].dataSourceName + '(' + dataSourceList[i].dataSourceType + ')'
                            + '</option>');
                    }
                }
                select_html += (option_html + "</select></div>");
                $('#datasourceDivElement').html(select_html);
                if (isExample) {
                    $('#datasourceSelectElement').attr('disabled', 'disabled');
                }
            } else {
                //alert(operType + " save fail");
                layer.msg("Load fail", {icon: 2, shade: 0, time: 2000});
                console.log("Load fail");
            }
        },
        error: function (request) {//Operation after request failure
            return;
        }
    });
}

//fill datasource
function fillDatasource(datasource, stop_id, stops_page_id) {
    var datasourceId = $(datasource).val();
    if (stop_id) {
        ajaxRequest({
            type: "POST",
            url: "/datasource/fillDatasource",
            async: true,
            data: {"dataSourceId": datasourceId, "stopId": stop_id},
            success: function (data) {//Operation after request successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg("update success", {icon: 1, shade: 0, time: 1000}, function () {
                        queryStopsProperty(stops_page_id, loadId);
                    });
                } else {
                    layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
                    console.log(dataMap.errorMsg);
                }
            },
            error: function (request) {//Operation after request failure
                return;
            }
        });
    } else {
        layer.msg("failed, stopId is null or datasourceId is null", {icon: 2, shade: 0, time: 2000});
    }
}

//Save XML file and related information
function saveXml(paths, operType, cells) {
    var getXml = thisEditor.getGraphXml();
    var xml_outer_html = getXml.outerHTML;
    var time, time1
    ajaxRequest({
        type: "POST",
        url: "/mxGraph/saveDataForTask",
        async: true,
        data: {
            imageXML: xml_outer_html,
            load: loadId,
            operType: operType
        },
        success: function (data) {//After the request is successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                console.log(operType + " save success");
                if (graphGlobal.isEnabled()) {
                    graphGlobal.startEditingAtCell();
                }
                thisEditor.setModified(false);
                if (operType && '' !== operType) {
                    //获取port
                    getStopsPortNew(paths);
                }
                if ("REMOVED" === operType) {
                    queryFlowInfo(loadId);
                } else if ("ADD" === operType) {
                    xmlDate = dataMap.xmlData;
                    loadXml(xmlDate, cells);
                }
            } else {
                //alert(operType + " save fail");
                layer.msg(operType + " save fail", {icon: 2, shade: 0, time: 2000});
                console.log(operType + " save fail");
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            }

        },
        error: function (request) {
            return;
        }
    });
}

//get port
function getStopsPortNew(paths) {
    if (!paths || null === paths || paths.length <= 0) {
        return;
    }
    pathsCells = paths;
    if (pathsCells.length > 1) {
        graphGlobal.removeCells(pathsCells);
        return;
    }
    var sourceMxCellId = '';
    var targetMxCellId = '';
    var pathLine = pathsCells[0];
    var pathLineId = pathLine.id;
    var sourceMxCell = pathLine.source;
    var targetMxCell = pathLine.target;
    if (targetMxCell) {
        sourceMxCellId = sourceMxCell.id;
    }
    if (targetMxCell) {
        targetMxCellId = targetMxCell.id;
    }
    ajaxRequest({
        cache: true,
        type: "get",
        url: "/stops/getStopsPort",
        data: {
            "flowId": loadId,
            "sourceId": sourceMxCellId,
            "targetId": targetMxCellId,
            "pathLineId": pathLineId
        },
        async: true,
        traditional: true,
        error: function (request) {
            console.log("error");
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                var showHtml = $('#portShowDiv').clone();
                showHtml.find('#portInfo1Copy').attr('id', 'portInfo');
                showHtml.find('#sourceTitle1Copy').attr('id', 'sourceTitle');
                showHtml.find('#sourceTitleStr1Copy').attr('id', 'sourceTitleStr');
                showHtml.find('#sourceTitleName').attr('id', 'sourceTitleName');
                showHtml.find('#sourceTitleCheckbox1Copy').attr('id', 'sourceTitleCheckbox');
                showHtml.find('#sourceTitleBtn1Copy').attr('id', 'sourceTitleBtn');
                showHtml.find('#sourceCrtPortId1Copy').attr('id', 'sourceCrtPortId');
                showHtml.find('#sourceCrtPortBtnId1Copy').attr('id', 'sourceCrtPortBtnId');
                showHtml.find('#sourceTypeDiv1Copy').attr('id', 'sourceTypeDiv');
                showHtml.find('#sourceRouteFilterList1Copy').attr('id', 'sourceRouteFilterList');
                showHtml.find('#sourceRouteFilterSelect1Copy').attr('id', 'sourceRouteFilterSelect');
                showHtml.find('#targetTitle1Copy').attr('id', 'targetTitle');
                showHtml.find('#targetTitleStr1Copy').attr('id', 'targetTitleStr');
                showHtml.find('#targetTitleName').attr('id', 'targetTitleName');
                showHtml.find('#targetTitleCheckbox1Copy').attr('id', 'targetTitleCheckbox');
                showHtml.find('#targetTitleBtn1Copy').attr('id', 'targetTitleBtn');
                showHtml.find('#targetCrtPortId1Copy').attr('id', 'targetCrtPortId');
                showHtml.find('#targetCrtPortBtnId1Copy').attr('id', 'targetCrtPortBtnId');
                showHtml.find('#targetTypeDiv1Copy').attr('id', 'targetTypeDiv');
                showHtml.find('#targetRouteFilterList1Copy').attr('id', 'targetRouteFilterList');
                showHtml.find('#targetRouteFilterSelect1Copy').attr('id', 'targetRouteFilterSelect');

                showHtml.find('#sourceCrtPortBtnId').attr('onclick', 'crtAnyPort("sourceCrtPortId",true)');
                showHtml.find('#targetCrtPortBtnId').attr('onclick', 'crtAnyPort("targetCrtPortId",false)');
                showHtml.find('#targetTitleBtn').hide();
                showHtml.find('#targetRouteFilterList').hide();
                showHtml.find('#sourceTitleBtn').hide();
                showHtml.find('#sourceRouteFilterList').hide();

                var sourceType = dataMap.sourceType;
                var targetType = dataMap.targetType;
                var sourceTypeStr = sourceType.text;
                var targetTypeStr = targetType.text;
                //Determine the number of available ports. If the number of available ports is not greater than 0, delete the line directly
                if (dataMap.sourceCounts > 0 && dataMap.targetCounts > 0) {
                    // Get a detailed use of the source port
                    var sourcePortUsageMap = dataMap.sourcePortUsageMap;
                    if (sourcePortUsageMap) {
                        showHtml.find('#sourceTitleCheckbox').html("");
                        var title = 'port：';
                        if (Object.keys(sourcePortUsageMap).length === 0) {
                            // return false // 如果为空,返回false
                        }else {
                            showHtml.find('#sourceTitleCheckbox').append(title);
                        }

                        for (portName in sourcePortUsageMap) {
                            var portNameVal = sourcePortUsageMap[portName];
                            var portCheckDiv = '<div id="' + portName + 'Checkbox" class="addCheckbox">'
                                + '<input id="' + portName + '" name="' + portName + '" type="checkbox" class="addCheckbox" value="' + portName + '"' + (!portNameVal ? 'checked="checked" disabled="disabled"' : '') + '/>'
                                + '<span class="addCheckbox ' + portName + '" disabled="' + !portNameVal + '">' + portName + '</span>'
                                + '</div>';
                            showHtml.find('#sourceTitleCheckbox').append(portCheckDiv);
                        }
                        // Add a create button when the type is Any
                        if ('Any' === sourceTypeStr) {
                            showHtml.find('#sourceTitleBtn').show();
                        } else if ('Route' === sourceTypeStr) {
                            showHtml.find('#sourceRouteFilterList').show();
                            if (dataMap.sourceFilter) {
                                var sourceFilters = dataMap.sourceFilter;
                                var selectOptionHtml = '<option value="">Please click Select Filter Country</option>';
                                for (var i = 0; i < sourceFilters.length; i++) {
                                    var sourceFilter = sourceFilters[i];
                                    selectOptionHtml += '<option value="' + sourceFilter.name + '" title="' + sourceFilter.customValue + '">' + sourceFilter.name + '</option>';
                                }
                                showHtml.find('#sourceRouteFilterSelect').html(selectOptionHtml);
                            } else {
                                showHtml.find('#sourceRouteFilterSelect').parent().html("Route no filter rule");
                            }
                        }
                    }
                    showHtml.find('#sourceTypeDiv').html(sourceTypeStr);
                    showHtml.find('#sourceTitleStr').html('From：');
                    showHtml.find('#sourceTitleName').html('stopName：' + dataMap.sourceName);
                    // Gets the detailed use of the target port
                    var targetPortUsageMap = dataMap.targetPortUsageMap;
                    if (targetPortUsageMap) {
                        showHtml.find('#targetTitleCheckbox').html("");
                        for (portName in targetPortUsageMap) {
                            var portNameVal = targetPortUsageMap[portName];
                            var portCheckDiv = '<div id="' + portName + 'Checkbox" class="addCheckbox">'
                                + '<input style="margin-right: 5px" id="' + portName + '" name="' + portName + '" type="checkbox" class="addCheckbox" value="' + portName + '"' + (!portNameVal ? 'checked="checked" disabled="disabled"' : '') + '/>'
                                + '<span class="addCheckbox ' + portName + '" disabled="' + !portNameVal + '">' + portName + '</span>'
                                + '</div>';
                            showHtml.find('#targetTitleCheckbox').append(portCheckDiv);
                        }
                        // Add a create button when the type is Any
                        if ('Any' === targetTypeStr) {
                            showHtml.find('#targetTitleBtn').show();
                        } else if ('Route' === targetTypeStr) {
                            showHtml.find('#targetRouteFilterList').show();
                            if (dataMap.targetFilter) {
                                var targetFilters = dataMap.targetFilter;
                                var selectOptionHtml = '<option value="">Please click Select Filter Country</option>';
                                for (var i = 0; i < targetFilters.length; i++) {
                                    var targetFilter = targetFilters[i];
                                    selectOptionHtml += '<option value="' + targetFilter.name + '" title="' + targetFilter.customValue + '">' + targetFilter.name + '</option>';
                                }
                                showHtml.find('#targetRouteFilterSelect').html(selectOptionHtml);
                            } else {
                                showHtml.find('#targetRouteFilterSelect').parent().html("Route no filter rule");
                            }
                        }
                    }
                    showHtml.find('#targetTypeDiv').html(targetTypeStr);
                    showHtml.find('#targetTitleStr').html('To：');
                    showHtml.find('#targetTitleName').html('stopName：' + dataMap.targetName);

                    if ("Default" === sourceTypeStr && "Default" === targetTypeStr) {
                    } else if ("None" === sourceTypeStr || "None" === targetTypeStr) {
                    } else {
                        layer.open({
                            type: 1,
                            title: '<span style="color: #269252;">CreatePort</span>',
                            shadeClose: false,
                            closeBtn: 0,
                            shift: 7,
                            area: ['580px', ''], //Width height
                            skin: 'layui-layer-rim', //Add borders
                            content: showHtml.html()
                        });
                    }
                } else {
                    graphGlobal.removeCells(pathsCells);
                }
            } else {
                graphGlobal.removeCells(pathsCells);
            }
        }
    });

}

//create any port
function crtAnyPort(crtPortInputId, isSource,type) {
    var crtProtInput = $('#' + crtPortInputId);
    var portNameVal = crtProtInput.val();
    if (portNameVal && '' !== portNameVal) {
        // if (!document.getElementById(portNameVal)) {
        if ($('#'+type).find('#'+portNameVal).length===0) {
            // var obj = '<div style="display: block;margin: 5px 0; border-bottom: 1px dashed rgb(204, 204, 204); padding: 2px 4px" class="addCheckbox" id="jCheckbox">'
            //     + '<input style="margin-right:5px" type="checkbox" checked = "checked" class="addCheckbox" id="' + portNameVal + '" name="' + portNameVal + '" value="' + portNameVal + '">'
            //     + '<span class="' + portNameVal + '">' + portNameVal + '</span>'
            //     + '</div>';
            // if (isSource) {
            //     $('#sourceTitleCheckbox').append(obj);
            // } else {
            //     $('#targetTitleCheckbox').append(obj);
            // }
            $('.' + portNameVal).text(portNameVal);
            return true;
        } else {
            layer.msg("Port name occupied!!", {icon: 2, shade: 0, time: 2000});
            return false;
        }
    } else {
        //alert("The port name cannot be empty");
        layer.msg("Port name cannot be empty", {icon: 2, shade: 0, time: 2000});
    }
}

//cancel port and path
function cancelPortAndPathNew() {
    layer.closeAll();
    graphGlobal.removeCells(graphGlobal.getSelectionCells());
}

// check choose port data
function checkChoosePort() {
    var sourcePortVal = '';
    var targetPortVal = '';
    var sourceTypeDiv = $('#sourceTypeDiv');
    var targetTypeDiv = $("#targetTypeDiv");
    if (!sourceTypeDiv && !targetTypeDiv) {
        layer.msg("Page error, please check!", {icon: 2, shade: 0, time: 2000});
        return false;
    }
    var isSourceRoute = false;
    var isTargetRoute = false;
    var sourceTitleCheckbox = $('#sourceTitleCheckbox');
    var targetTitleCheckbox = $("#targetTitleCheckbox");
    if (sourceTitleCheckbox) {
        var sourceDivType = sourceTypeDiv.html();
        if ('Default' === sourceDivType) {
            //'default' type is not verified
        } else if ("Route" === sourceDivType) {
            isSourceRoute = true;
            //'Route' type is not verified
        } else {
            var sourceEffCheckbox = [];
            sourceTitleCheckbox.find("input[type='checkbox']:checked").each(function () {
                if ($(this).prop("disabled") == false) {
                    sourceEffCheckbox[sourceEffCheckbox.length] = $(this);
                }
            });
            var sourceProtInput = $('#sourceCrtPortId');
            var sourceNameVal = sourceProtInput.val();

            if (sourceEffCheckbox.length > 1) {
                layer.msg("'sourcePort'can only choose one", {icon: 2, shade: 0, time: 2000});
                return false;
            }
            // if (sourceEffCheckbox < 1) {
            if (sourceEffCheckbox.length < 1 && !sourceNameVal) {
                layer.msg("Please select'sourcePort'", {icon: 2, shade: 0, time: 2000});
                return false;
            }

            if (!!sourceNameVal){
                let whetherThrough = crtAnyPort("sourceCrtPortId",true,'sourceTitle');
                if (whetherThrough){
                    sourcePortVal = sourceNameVal;
                }else
                    return ;
            }else {
                for (var i = 0; i < sourceEffCheckbox.length; i++) {
                    var sourcecheckBoxEff = sourceEffCheckbox[i];
                    if ('' === sourcePortVal) {
                        sourcePortVal = sourcecheckBoxEff.val();
                    } else {
                        sourcePortVal = sourcePortVal + "," + sourcecheckBoxEff.val();
                    }
                }
            }

        }
    } else {
        layer.msg("Page error, please check!", {icon: 2, shade: 0, time: 2000});
        return false;
    }
    if (targetTitleCheckbox) {
        var targetDivType = targetTypeDiv.html();
        if ('Default' === targetDivType) {
            //Default type not checked
        } else if ("Route" === targetDivType) {
            isTargetRoute = true;
            //Route type not checked
        } else {
            var targetEffCheckbox = [];
            targetTitleCheckbox.find("input[type='checkbox']:checked").each(function () {
                if ($(this).prop("disabled") == false) {
                    targetEffCheckbox[targetEffCheckbox.length] = $(this);
                }
            });
            let targetProtInput = $('#targetCrtPortId');
            let targetNameVal = targetProtInput.val();

            if (targetEffCheckbox.length > 1) {
                layer.msg("'targetPort'can only choose one", {icon: 2, shade: 0, time: 2000});
                return false;
            }
            // if (targetEffCheckbox.length < 1) {
            if (targetEffCheckbox.length < 1 && !targetNameVal) {
                layer.msg("Please select'targetPort'", {icon: 2, shade: 0, time: 2000});
                return false;
            }

            if (!!targetNameVal){
                let whetherThrough =  crtAnyPort("targetCrtPortId",false,'targetTitle');
                if (whetherThrough){
                    targetPortVal = targetNameVal;
                }else
                    return ;
            }else {
                for (var i = 0; i < targetEffCheckbox.length; i++) {
                    var targetcheckBoxEff = targetEffCheckbox[i];
                    if ('' === targetPortVal) {
                        targetPortVal = targetcheckBoxEff.val();
                    } else {
                        targetPortVal = targetPortVal + "," + targetcheckBoxEff.val();
                    }
                }
            }

        }
    } else {
        layer.msg("Page error, please check!", {icon: 2, shade: 0, time: 2000});
        return false;
    }

    var sourceMxCellId = '';
    var targetMxCellId = '';
    var pathLine = pathsCells[0];
    var pathLineId = pathLine.id;
    var sourceMxCell = pathLine.source;
    var targetMxCell = pathLine.target;
    if (targetMxCell) {
        sourceMxCellId = sourceMxCell.id;
    }
    if (targetMxCell) {
        targetMxCellId = targetMxCell.id;
    }
    var sourceRouteFilterSelectValue = $('#sourceRouteFilterSelect').val();
    var targetRouteFilterSelectValue = $('#targetRouteFilterSelect').val();
    var reqData = {
        "flowId": loadId,
        "pathLineId": pathLineId,
        "sourcePortVal": sourcePortVal,
        "targetPortVal": targetPortVal,
        "sourceId": sourceMxCellId,
        "targetId": targetMxCellId,
        "sourceFilter": sourceRouteFilterSelectValue,
        "targetFilter": targetRouteFilterSelectValue,
        "sourceRoute": isSourceRoute,
        "targetRoute": isTargetRoute
    }
    return reqData;
}

//choose port
function choosePortNew() {
    if (pathsCells.length > 1) {
        graphGlobal.removeCells(pathsCells);
        layer.msg("Page error, please check!", {icon: 2, shade: 0, time: 2000}, function () {
            layer.closeAll();
        });
        return false;
    } else {
        var reqData = checkChoosePort();
        if (reqData) {
            ajaxRequest({
                cache: true,
                type: "get",
                url: "/path/savePathsPort",
                data: reqData,
                async: true,
                traditional: true,
                error: function (request) {
                    console.log("error");
                    return;
                },
                success: function (data) {
                    var dataMap = JSON.parse(data);
                    //alert(dataMap);
                    if (200 === dataMap.code) {
                        layer.closeAll();
                    } else {
                        //alert("Port Selection Save Failed");
                        layer.msg("Port Selection Save Failed", {icon: 2, shade: 0, time: 2000}, function () {
                            layer.closeAll();
                        });
                        graphGlobal.removeCells(pathsCells);
                    }
                }
            });
        }
    }
}

// add MxCell operation
function addMxCellOperation(evt) {
    var cells = evt.properties.cells;
    statusgroup = cells[0].value;

    var removeCellArray = [];
    var paths = [];
    cells.forEach(cellFor => {
        if (cellFor && cellFor.edge) {
            var cellForSource = cellFor.source;
            var cellForTarget = cellFor.target;
            if (cellForSource && cellForTarget
                && (cellForSource.style && (cellForSource.style).indexOf("text\;") !== 0)
                && (cellForTarget.style && (cellForTarget.style).indexOf("text\;") !== 0)) {
                paths[paths.length] = cellFor;
            } else {
                removeCellArray.push(cellFor);
            }
        } else if (cellFor.style && (cellFor.style).indexOf("image\;") === 0) {
            if (!removegroupPaths) {
                removegroupPaths = [];
            }
            removegroupPaths.push(cellFor);
        }
    });
    graphGlobal.removeCells(removeCellArray);
    if (cells.length != removeCellArray.length) {
        saveXml(paths, 'ADD', evt.properties.cells);
    }
    if ('cellsAdded' == evt.name) {
        consumedFlag = evt.consumed ? true : false;
        flowMxEventClickFunc(evt.properties.cell, consumedFlag);
    }
}

// moved MxCell operation
function movedMxCellOperation(evt) {
    let evtCellsArr =  evt.properties.cells;
    if(evtCellsArr.length === 1 && evtCellsArr[0].edge == 1) {
        console.log("Connect Line MOVE");
    }
    statusgroup = ""
    if (evt.properties.disconnect) {
        saveXml(null, 'MOVED');   // preservation method
    }
    consumedFlag = evt.consumed ? true : false;
    flowMxEventClickFunc(evt.properties.cell, consumedFlag);
}

// remove MxCell operation
function removeMxCellOperation(evt) {
    saveXml(null, 'REMOVED');
}

//update stops name button
function isShowUpdateStopsName(flag) {
    if (flag) {
        $("#input_stopsVo_name").val($("#span_stopsVo_name").text());
        $("#tr_stopsVo_name_info").hide();
        $("#tr_stopsVo_name_input").show();
    } else {
        $("#tr_stopsVo_name_input").hide();
        $("#tr_stopsVo_name_info").show();
    }
}

//delete last reload data
function deleteLastReloadData(stopId) {
    ajaxRequest({
        type: "POST",//Request type post
        url: "/stops/deleteLastReloadData",//This is the name of the file where I receive data in the background.
        data: {stopId: stopId},
        error: function (request) {//Operation after request failure
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 == dataMap.code) {
                layer.msg(dataMap.errorMsg, {
                    icon: 1,
                    shade: 0,
                    time: 2000
                }, function () {
                    $("#del_last_reload_div").hide();
                    $("#del_last_reload_table").hide();
                });
            } else {
                layer.msg(dataMap.errorMsg, {
                    icon: 2,
                    shade: 0,
                    time: 2000
                }, function () {

                });
            }
        }
    });
}

//Example
function prohibitEditing(evt, operationType) {
    if ('ADD' === operationType || 'REMOVED' === operationType) {
        var msgStr = "This is an example, you can't add, edit or delete";
        layer.msg(msgStr, {icon: 2, shade: 0, time: 2000});
    } else if ('MOVED' === operationType) {
        flowMxEventClickFunc(evt.properties.cell, false);
    }
    ajaxRequest({
        type: "POST",//Request type post
        url: "/mxGraph/eraseRecord",
        data: {},
        async: true,
        error: function (request) {//Operation after request failure
            if ('ADD' === operationType || 'REMOVED' === operationType) {
                location.reload();
            }
            eraseRecord()
            return;
        },
        success: function (data) {//After the request is successful
            if ('ADD' === operationType || 'REMOVED' === operationType) {
                location.reload();
            }
            eraseRecord()
        }
    });
}

//save checkpoints
function saveCheckpoints(stopId) {
    var isCheckpoint = 0;
    if ($('#isCheckpoint').is(':checked')) {
        isCheckpoint = 1;
    }
    ajaxRequest({
        cache: true,
        type: "POST",
        url: "/stops/updateStopsById",
        data: {
            stopId: stopId,
            isCheckpoint: isCheckpoint
        },
        async: true,
        traditional: true,
        error: function (request) {
            layer.msg("Failure to mark'Checkpoint'", {icon: 2, shade: 0, time: 2000});
            return;
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg("Successful modification of the tag'Checkpoint'", {
                    icon: 1,
                    shade: 0,
                    time: 2000
                }, function () {
                });
            } else {
                layer.msg("Failed to modify the tag'Checkpoint'", {icon: 2, shade: 0, time: 2000});
            }

        }
    });
}

//update stops Name button
function updateStopsName() {
    if ($("#span_stopsVo_name").text() === $("#input_stopsVo_name").val()) {
        isShowUpdateStopsName(false);
        return;
    }
    ajaxRequest({
        type: "POST",
        url: "/stops/updateStopsNameById",
        async: true,
        data: {
            flowId: loadId,
            stopId: $("#input_flowStopsVo_id").val(),
            pageId: $("#input_flowStopsVo_pageId").val(),
            name: $("#input_stopsVo_name").val()
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                //reload xml
                var xml = mxUtils.parseXml(dataMap.XmlData);
                var node = xml.documentElement;
                var dec = new mxCodec(node.ownerDocument);
                dec.decode(node, graphGlobal.getModel());
                var s_cell = graphGlobal.getModel().getCell($("#input_flowStopsVo_pageId").val());
                graphGlobal.addSelectionCell(s_cell);
                layer.msg("attribute update success", {icon: 1, shade: 0, time: 2000}, function () {
                });
                $("#span_stopsVo_name").text($("#input_stopsVo_name").val());
                isShowUpdateStopsName(false);
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            }
        },
        error: function (request) {
            console.log("attribute update error");
            layer.msg("attribute update error", {icon: 2, shade: 0, time: 2000});
            return;
        }
    });
}

//update stops property
function openUpdateStopsProperty(e, isCustomized, language, isLocked) {
    if (isLocked)
        return;

    var stopOpenTemplateClone = $("#stopOpenTemplate").clone();
    stopOpenTemplateClone.find("#stopValue").attr("id", "stopAttributesValue");
    stopOpenTemplateClone.find("#buttonStop").attr("id", "stopAttributesValueBtn");
    var locked = e.getAttribute('locked');
    if (isExample || 'true' == locked) {
        stopOpenTemplateClone.find("#stopAttributesValue").attr("disabled", "disabled");
        stopOpenTemplateClone.find("#stopAttributesValueBtn").hide();
    }
    var id = e.getAttribute('id');
    var name = e.getAttribute('name');
    var value = e.getAttribute('data');
    stopOpenTemplateClone.find("#stopAttributesValue").css("background-color", "");
    stopOpenTemplateClone.find("#stopAttributesValue").attr('name', name);
    stopOpenTemplateClone.find("#stopAttributesValue").text(value);
    var funcStr = '';
    if (isCustomized) {
        funcStr = "updateStopsCustomizedProperty('" + id + "','stopAttributesValue',this);";
    } else {
        funcStr = "updateStopsProperty('" + id + "','stopAttributesValue',this);";
    }
    stopOpenTemplateClone.find("#stopAttributesValueBtn").attr("onclick", funcStr);
    var p = $(e).offset();
    // var openWindowCoordinate = [(p.top + 34) + 'px', (document.body.clientWidth - 300) + 'px'];
    var openWindowCoordinate = [(p.top + 34) + 'px', 77 + 'vw'];
    // console.log(openWindowCoordinate);
    // layer.open({
    //     type: 1,
    //     title: name,
    //     shadeClose: true,
    //     closeBtn: 1,
    //     shift: 7,
    //     anim: 5,//Pop up from top
    //     shade: 0.1,
    //     resize: true,//No stretching
    //     //move: false,//No dragging
    //     offset: openWindowCoordinate,//coordinate
    //     area: ['22vw;', '250px'], //Width Height
    //     content: stopOpenTemplateClone.html()
    // });
    openRightHelpPage(value,id,language,name);
    $("#stopValue").focus();
    $("#stopAttributesValue").focus();
    if ($("#stopAttributesValue").text()) {
        $("#stopAttributesValue")[0].selectionStart = $("#stopAttributesValue").text().length;
    }
}
var openRightHelpPage = function(value,id,language,name){
    // 判断页面是否加载完毕
    if(document.readyState === 'complete') {
        window.parent['openRightHelpPage'](value,id,language,name);
    }
}
//update stops property select
function updateStopsProperty(stopsPropertyId, property_name_id, type) {
    if (stopsPropertyId.length <= 0) {
        console.log("stopsPropertyId is null ");
        return;
    }
    if (property_name_id == null || property_name_id.length <= 0) {
        console.log("property name id is null ");
        return;
    }
    var content = document.getElementById('' + property_name_id + '').value;
    var classname = $('#' + property_name_id).attr('data-toggle');
    //If the modification is empty and it is a text box, the modification operation will not be performed;
    if (content == "" && type == "input" && classname == 'true') {
        $("#" + property_name_id + "").css("background-color", "#FFD39B");
        return;
    } else if (content == "" && type == "select") {
        content = "-1";
    }
    $("#" + property_name_id + "").css("background-color", "");
    ajaxRequest({
        type: "POST",
        url: "/stops/updateStopsOne",
        async: true,
        data: {
            "id": stopsPropertyId,
            "content": content
        },
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                $("#" + stopsPropertyId).val(dataMap.value);
                $("#" + stopsPropertyId).attr("data", dataMap.value);
                // layer.msg("update success", {icon: 1, shade: 0, time: 1000}, function () {
                layer.closeAll();
                // });
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                });
            }
        },
        error: function (request) {
            console.log("error");
            return;
        }
    });
}

// set stops customized table html
function setCustomizedTableHtml(stopPageId, stopsCustomizedPropertyVo, stopOutPortType) {
    var isRouter = false;
    if (stopOutPortType && stopOutPortType.stringValue === "ROUTE") {
        isRouter = true;
    }
    var table_tr = "";
    if (stopsCustomizedPropertyVo) {
        table_tr = '<tr class="trTableCustomizedStopProperty">'
            + '<td style="width: 60px;">'
            + '<span style="margin-left: 10px;">' + stopsCustomizedPropertyVo.name + ': </span>'
            + '</td>'
            + '<td style="width: 25px;">'
            + '<img src="' + web_drawingBoard + '/img/descIcon.png" title="' + stopsCustomizedPropertyVo.description + '" style="cursor: pointer;">'
            + '</td>'
            + '<td>'
            + '<input data-toggle="true"class="form-control"'
            + 'id="' + stopsCustomizedPropertyVo.id + '"'
            + 'name="' + stopsCustomizedPropertyVo.name + '" '
            + 'value="' + stopsCustomizedPropertyVo.customValue + '" '
            + 'onclick="openUpdateStopsProperty(this,true)"readonly="readonly" value=""style="background: rgb(245, 245, 245);">'
            + '</td>'
            + '<td>'
            + '<span style="color:red">*</span>'
            + '<a style="float:right;margin-right: 10px" class="btn" href="javascript:removeStopCustomProperty(\'' + stopPageId + '\',\'' + stopsCustomizedPropertyVo.id + '\',' + isRouter + ');"><i class="glyphicon glyphicon-remove" style="color: red;"></i></a>'
            + '</td>'
            + '</tr>';
    }
    return table_tr;

}

//open add stops custom property page
function openAddStopCustomAttrPage(stopId) {
    var addStopCustomizedAttrOpenTemplate = $("#addStopCustomizedAttrOpenTemplate").clone();
    addStopCustomizedAttrOpenTemplate.find("form").attr("id", "openAddStopCustomAttrId");
    addStopCustomizedAttrOpenTemplate.find("#openAddCustomizedWindowStopId").hide();
    addStopCustomizedAttrOpenTemplate.find("#openAddCustomizedWindowStopId").attr("value", stopId);
    layer.open({
        type: 1,
        title: "Add Customized Property",
        shadeClose: true,
        closeBtn: 1,
        shift: 7,
        anim: 5,//Bounce up and down
        shade: 0.1,
        // resize: false,//No stretch
        // move: false,//No drag and drop
        // offset: ['' + p.top + 'px', '' + p.left + 'px'],//coordinate
        area: ['555px', '340px'], //Width height
        content: addStopCustomizedAttrOpenTemplate.html()
    });
}

//add stops custom property
function addStopCustomProperty(reqData) {
    ajaxRequest({
        type: "POST",
        url: "/stops/addStopCustomizedProperty",
        async: true,
        data: reqData,
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg("add success", {icon: 1, shade: 0, time: 1000}, function () {
                    layer.closeAll();
                    queryStopsProperty(dataMap.stopPageId, loadId);
                });
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                });
            }
        },
        error: function (request) {//Operation after request failure
            return;
        }
    });

}

function updateStopsCustomizedProperty(id, name, e) {
    var p = $(e).offset();
    var content = document.getElementById('' + name + '').value;
    var classname = $('#' + id).attr('data-toggle');
    if (content == "") {
        if (classname == 'true') {
            $("#" + name + "").css("background-color", "#FFD39B");
            $("#" + name + "").focus();
        }
        return;
    }
    ajaxRequest({
        type: "POST",
        url: "/stops/updateStopsCustomizedProperty",
        data: {
            "id": id,
            "customValue": content
        },
        async: true,
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
                $("#" + id).val(dataMap.value);
            } else {
                layer.msg('', {icon: 2, shade: 0, time: 2000}, function () {
                });
            }
            layer.closeAll('page');
            console.log("attribute update success");
        }
    });
}

//remove stops custom property
function removeStopCustomProperty(stopPageId, customPropertyId, isRouter) {
    if (isRouter) {
        getRouterAllPaths(stopPageId, customPropertyId)
    } else {
        ajaxRequest({
            type: "POST",//Request type post
            url: "/stops/deleteStopsCustomizedProperty",//This is the name of the file where I receive data in the background.
            data: {customPropertyId: customPropertyId},
            error: function (request) {//Operation after request failure
                return;
            },
            success: function (data) {//Operation after request successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg("add success", {icon: 1, shade: 0, time: 1000}, function () {
                        layer.closeAll();
                        queryStopsProperty(stopPageId, loadId);
                    });
                } else {
                    layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                    });
                }
            }
        });
    }
}

function getRouterAllPaths(stopPageId, customPropertyId) {
    removeRouterStopCustomProperty(stopPageId, customPropertyId);
    return;
    ajaxRequest({
        type: "POST",//Request type post
        url: "/stops/getRouterStopsCustomizedProperty",//This is the name of the file where I receive data in the background.
        data: {customPropertyId: customPropertyId},
        error: function (request) {//Operation after request failure
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                if (dataMap.pathsVoList) {
                    var showPathsHtml = '<span>Deleting this rule will affect the following:</span>';
                    layer.confirm(showPathsHtml, {icon: 1, shade: 0, time: 1000}, function () {
                    });
                } else {
                    //removeRouterStopCustomProperty(stopPageId, customPropertyId);
                }
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                });
            }
        }
    });
}

function removeRouterStopCustomProperty(stopPageId, customPropertyId) {
    ajaxRequest({
        type: "POST",//Request type post
        url: "/stops/deleteRouterStopsCustomizedProperty",//This is the name of the file where I receive data in the background.
        data: {customPropertyId: customPropertyId},
        error: function (request) {//Operation after request failure
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg("delete success", {icon: 1, shade: 0, time: 1000}, function () {
                    layer.closeAll();
                    queryStopsProperty(stopPageId, loadId);
                });
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                });
            }
        }
    });
}

// Click Slider
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

//Request interface to reload'stops'
function reloadStops() {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        data: {"load": loadId},
        cache: true,//Keep cached data
        type: "POST",//Request type post
        url: "/stops/reloadStops",
        error: function (request) {//Operation after request failure
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            //alert("reload fail");
            layer.msg("reload fail", {icon: 2, shade: 0, time: 2000}, function () {
            });
            return;
        },
        success: function (data) {//Operation after request successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                window_location_href("/page/flow/mxGraph/index.html?drawingBoardType=TASK&load=" + dataMap.load + "&_" + new Date().getTime());
            } else {
                //alert("reload fail");
                layer.msg("reload fail", {icon: 2, shade: 0, time: 2000}, function () {
                });
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            }
        }
    });
}

//open template list
function openTemplateList() {
    if (isExample) {
        layer.msg('This is an example, you can\'t edit', {icon: 2, shade: 0, time: 2000});
        return;
    }
    var url = "";
    var functionNameStr = "";
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

//save template
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
                templateType: "TASK"
            },
            async: true,
            error: function (request) {//Operation after request failure
                console.log(" save template error");
                return;
            },
            success: function (data) {//After the request is successful
                var dataMap = JSON.parse(data);
                if (200 === dataMap.code) {
                    layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000});
                } else {
                    layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
                }
            }
        });
    });
}

//upload template
function uploadTemplate() {
    document.getElementById("uploadFile").click();
}

//file type check
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

//upload template file
function uploadTemplateFile(element) {
    if (!FileTypeCheck(element)) {
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
        success: function (data) {
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000});
            } else {
                layer.msg(dataMap.errorMsg, {icon: 2, shade: 0, time: 2000});
            }
        },
        error: function () {
            layer.msg("Upload failure", {icon: 2, shade: 0, time: 2000});
        }
    });
}

//load template list
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

//load template xml
function loadingXml(id, loadId) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        type: 'post',
        data: {
            loadType: "TASK",
            templateId: id,
            load: loadId
        },
        async: true,
        url: "/flowTemplate/loadingXmlPage",
        success: function (data) {
            var dataMap = JSON.parse(data);
            var icon_code = 2;
            if (200 === dataMap.code) {
                icon_code = 1;
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
            layer.msg(dataMap.errorMsg, {icon: icon_code, shade: 0.7, time: 2000}, function () {
                window.location.reload();
            });
        },
        error: function () {
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        }
    });
}

//run
function runFlow(runMode) {
    // $('#fullScreen').show();
    window.parent.postMessage(true);
    ajaxRequest({
        type: "POST",
        url: "/flow/runFlow",
        async: true,
        data: {
            flowId: loadId,
            runMode: runMode
        },
        success: function (data) {//After the request is successful
            var dataMap = JSON.parse(data);
            if (200 === dataMap.code) {
                layer.msg(dataMap.errorMsg, {icon: 1, shade: 0, time: 2000}, function () {
                    //Jump to the monitor page after starting successfully
                    new_window_open("/page/process/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS&load=" + dataMap.processId);
                });
            } else {
                //alert("Startup failure：" + dataMap.errorMsg);
                layer.msg("Startup failure：" + dataMap.errorMsg, {icon: 2, shade: 0, time: 2000}, function () {
                });
            }
            // $('#fullScreen').hide();
            window.parent.postMessage(false);
        },
        error: function (request) {//Operation after request failure
            //alert("Request Failed");
            layer.msg("Request Failed", {icon: 2, shade: 0, time: 2000}, function () {
                // $('#fullScreen').hide();
                window.parent.postMessage(false);
            });
            return;
        }
    });
}

// run cells  runFollowUp
function RunFlowOrFlowCellsUp(includeEdges) {
    StopsComponentIsNeeedSourceData(stopsId, true)
}

var StopsComponentIsNeeedSourceData = function(id, isRunFollowUp){
    // 判断页面是否加载完毕
    if(document.readyState === 'complete') {
        window.parent['StopsComponentIsNeeedSourceData']({id: id, isRunFollowUp: isRunFollowUp});
    }

}

window.addEventListener("message",function(event){
    window.parent.postMessage(true);

    var data = event.data;
    //以下内容为处理业务和调用当前页面的函数方法
    if(data.pageURl){
        layer.msg(data.pageMsg, {icon: 1, shade: 0, time: 2000}, function () {
            //Jump to the monitor page after starting successfully
            new_window_open("/page/process/mxGraph/index.html?drawingBoardType=PROCESS&processType=PROCESS&load=" + data.pageURl);
        });
        window.parent.postMessage(false);

    }else {
        layer.msg("Startup failure：" + data.pageMsg, {icon: 2, shade: 0, time: 2000}, function () {
        });
        window.parent.postMessage(false);

    }
});

// run cells current
function RunFlowOrFlowCells(includeEdges) {
    StopsComponentIsNeeedSourceData(stopsId, false)

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
