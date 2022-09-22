// var web_header_prefix = "http://10.0.88.46:86/piflow";
var web_base_origin = window.location.origin;
var web_drawingBoard = "/drawingBoard";
var sever_base_origin = "http://10.0.85.80:6002/piflow-web";
// var basePath = window.sessionStorage.getItem("basePath")
var basePath = null;
// var token = top.window.sessionStorage.getItem('token') //此处放置请求到的用户token
var token = null;

if (document.cookie && document.cookie != '') {
    var cookies = document.cookie.split(';');//将获得的所有cookie切割成数组
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];//得到某下标的cookies数组
        if (cookie.substring(0, 'basePath'.length + 2).trim() == 'basePath='.trim()) {//如果存在该cookie的话就将cookie的值拿出来
            basePath = cookie.substring('basePath'.length + 2, cookie.length);
            // break
        }else if (cookie.substring(0, 'basePath'.length + 1).trim() == 'basePath='.trim()) {//如果存在该cookie的话就将cookie的值拿出来
            basePath = cookie.substring('basePath'.length + 1, cookie.length);
            // break
        }
        if (cookie.substring(0, 'token'.length + 2).trim() == 'token='.trim()) {
            token = cookie.substring('token'.length + 2, cookie.length);
            // break
        }
    }
}

var web_header_prefix = basePath.indexOf(window.location.origin) || basePath.indexOf('http') > -1 ? basePath : web_base_origin + basePath; //与 .env.production 内容同步
/**
 * ajax工具js
 * @param requestType 请求类型(get,post)
 * @param url 请求url
 * @param async 是否异步
 * @param requestData 请求参数
 * @param backFunc 请求成功后回调方法
 * @param errBackFunc 请求失败后回调方法
 */
function ajaxRequest(param) {
    if (!param.url) {
        throw "url is null"
    }
    var requestType = param.type ? param.type : "GET";
    var url = param.url;
    var cache = param.cache ? true : false;
    var async = param.async ? true : false;
    var traditional = param.traditional ? true : false;
    var requestData = param.data ? param.data : {};
    var backFunc = param.success;
    var errBackFunc = param.error;
    var processData = true;
    if (undefined !== param.processData) {
        processData = param.processData ? true : false;
    }
    var async = true;
    if (undefined !== param.async) {
        async = param.async ? true : false;
    }
    var contentType = "application/x-www-form-urlencoded;charset=UTF-8";
    if (undefined !== param.contentType) {
        contentType = param.contentType
    }
    $.ajax({
        cache: cache,
        type: requestType,
        async: async,
        url: web_header_prefix + url,
        data: requestData,
        traditional: traditional,
        contentType: contentType,
        processData: processData,
        headers: {
            Authorization: ("Bearer " + token)
        },
        // dataType: 'json',
        // beforeSend: function (request) {
        //     request.setRequestHeader("token", tokenInfo);
        // },
        // xhrFields: {
        //     withCredentials: true
        // },
        success: function (data) {
            //data =  JSON.parse(data);
            if (data.code === 403 || data.code === 401) {
                //  alert(data.errMsg);
                // console.log(data);
                window.location.href = web_base_origin + "/#/login";
                return;
            }
            if (backFunc && $.isFunction(backFunc)) {
                backFunc(data);
            }
        },
        error: function (request) {//请求失败之后的操作
            if (errBackFunc && $.isFunction(errBackFunc)) {
                errBackFunc(request);
            }
            return;
        }
    });
};

function ajaxLoad(elementId, requestUrl, backFunc, errBackFunc) {
    ajaxLoadAsync(elementId, requestUrl, true, backFunc, errBackFunc);
}

function ajaxLoadAsync(elementId, requestUrl, async, backFunc, errBackFunc) {
    async = (async === undefined) ? true : async;
    $.ajax({
        type: "GET",
        async: async,
        url: web_drawingBoard + requestUrl,
        headers: {
            Authorization: ("Bearer " + token)
        },
        success: function (data) {
            $("#" + elementId).html(data);
            if (backFunc && $.isFunction(backFunc)) {
                backFunc(data);
            }
        },
        error: function (request) {//请求失败之后的操作
            if (errBackFunc && $.isFunction(errBackFunc)) {
                errBackFunc(request);
            }
            return;
        }
    });

}

function ajaxFun(config) {
    if (config) {
        config.headers = {Authorization: ("Bearer " + token)};
        config.url = sever_base_origin + config.url;
    } else {
        console.log("ajax config error");
        layer.msg("ajax config error", {icon: 2, shade: 0, time: 2000});
    }
}

function getUrlParams(url) {
    var result = new Object();
    var idx = url.lastIndexOf('?');

    if (idx > 0) {
        var params = url.substring(idx + 1).split('&');

        for (var i = 0; i < params.length; i++) {
            idx = params[i].indexOf('=');

            if (idx > 0) {
                result[params[i].substring(0, idx)] = params[i].substring(idx + 1);
            }
        }
    }

    return result;
}

function openLayerWindowLoadHtml(htmlStr, window_width, window_height, title, shade) {
    shade = shade ? shade : 0;
    layer.open({
        type: 1,
        title: '<span style="color: #269252;">' + title + '</span>',
        shade: shade,
        shadeClose: false,
        closeBtn: 1,
        shift: 7,
        area: [window_width + 'px', window_height + 'px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: htmlStr
    });
}

function openLayerTypeIframeWindowLoadUrl(url, window_width, window_height, title, shade) {
    shade = shade ? shade : 0;
    layer.open({
        type: 2,
        title: '<span style="color: #269252;">' + title + '</span>',
        shade: shade,
        shadeClose: false,
        closeBtn: 1,
        shift: 7,
        area: [window_width + 'px', window_height + 'px'], //Width height
        skin: 'layui-layer-rim', //Add borders
        content: web_drawingBoard + url
    });
}

// window.location
function window_location_href(url) {
    window.top.location.href = window.location.origin + "/#/drawingBoard?src=" + web_drawingBoard + url ;
    // window.top.location.reload();
    // window.open(window.location.origin + "/#/drawingBoard?src=" + web_drawingBoard + url,"_blank");
}

function new_window_open(url) {
    var tempWindow = window.top.location.href = window.location.origin + "/#/drawingBoard?src=" + web_drawingBoard + url;

    // var tempWindow = window.open(window.location.origin + "/#/drawingBoard?src=" + web_drawingBoard + url);
    if (tempWindow == null || typeof (tempWindow) == 'undefined') {
        alert('The window cannot be opened. Please check your browser settings.')
    }

}

