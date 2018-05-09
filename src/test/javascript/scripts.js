/**
 * Created by bluejoe on 2018/5/8.
 */
//type javascripts in this file to use IDE formatter
var fun =
	function (s) {
		var arr = Array();
		var len = s.length;
		for (var i = 0; i < s.length - 1; i++) {
			arr.push(s.substring(i, i + 2));
		}

		return arr;
	}