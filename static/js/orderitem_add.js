//分类页根据分类名称自动生成url方法
$(function(){
	$('input[name=name]').change(function(){
        $('input[name=link]').val($.trim($(this).val()).toLowerCase().replace(/[^\b\w]+/g,'-'));
    });
})