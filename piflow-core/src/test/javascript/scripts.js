/**
 * Created by bluejoe on 2018/5/8.
 */
//type scripts here to use javascript formatter
[
	[
		function (row) {
			var arr = Array();
			var str = row.get(0);
			var len = str.length;
			for (var i = 0; i < len - 1; i++) {
				arr.push($.Row(str.substring(i, i + 2)));
			}

			return java.util.Arrays.asList($.Row(arr));
		}
		,
		function (row) {
			return $.Row(row.get(0).replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""));
		}
	]
]