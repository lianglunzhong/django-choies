$(function(){
	$('.no_limit_stock').bind('click',function(){
	    var stock = $(this).val();
	    if(stock == 0)
	    {
	        $('#product_stock').show();
	        $('#stock').val(-1);
	    }
	    if(stock == 1)
	    {
	        $('#product_stock').hide();
	        $('#stock').val(-99);
	    }
	});
})