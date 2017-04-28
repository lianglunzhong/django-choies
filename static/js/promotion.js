$(function(){
    $("#promotions_form").submit(function(){
        var discount_method = $("input[ name='discount_method']:checked").val();

        if(discount_method )
        {
            if(discount_method=='rate')
            {
                var rate = $("input[ name='rate']").val();
                if(!rate)
                {
                    alert('价格折扣不能为空');
                    return false;
                }
            }
            if(discount_method=='reduce')
            {
                var reduce = $("input[ name='reduce']").val();
                if(!reduce)
                {
                    alert('价格折扣不能为空');
                    return false;
                }
            }
             if(discount_method=='equal')
            {
                var equal = $("input[ name='equal']").val();
                if(!equal)
                {
                    alert('价格折扣不能为空');
                    return false;
                }
            }
             if(discount_method=='points')
            {
                var points = $("input[ name='points']").val();
                if(!points)
                {
                    alert('价格折扣不能为空');
                    return false;
                }
            }

        }

    });
});