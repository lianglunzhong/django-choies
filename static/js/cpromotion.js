$(function(){
    $("#cpromotions_form").submit(function(){
        var is_restrict = $("input[ name='is_restrict']:checked").val();

        var conditions = $("input[ name='conditions']:checked").val();
        var promotion_method = $("input[ name='promotion_method']:checked").val();
        if(is_restrict )
        {
         var restrictions = $("input[ name='restrictions']:checked").val();
            if(typeof(restrictions)== "undefined" )
            {
              alert('分类/产品限制不能为空！');
              return false;
            }else
            {
                if(restrictions=='restrict_catalog')
                {
                    var restrict_catalog = $("input[ name='restrict_catalog']").val();
                    if(!restrict_catalog)
                    {
                        alert('分类限制不能为空');
                        return false;
                    }
                }
                if(restrictions=='restrict_product')
                {
                    var restrict_product = $("input[ name='restrict_product']").val();
                    if(!restrict_product)
                    {
                        alert('产品限制不能为空');
                        return false;
                    }
                }
            }
        }
        if(typeof(conditions)== "undefined" )
        {
          alert('促销条件不能为空！');
          return false;
        }else
        {
             if(conditions=='sum')
            {
                var sum = $("input[ name='sum']").val();
                if(!sum)
                {
                    alert('金额不能为空');
                    return false;
                }
            }
            if(conditions=='quantity')
            {
                var quantity = $("input[ name='quantity']").val();
                if(!quantity)
                {
                    alert('数量不能为空');
                    return false;
                }
            }
        }

        if(typeof(promotion_method)=="undefined" )
        {
          alert('请选择促销方式！');
          return false;
        }else
        {
            //打折
            if(promotion_method=='discount')
            {
                discount_method = $("input[ name='discount_method']:checked").val();
                //打折条件选择
                if(typeof(discount_method)== "undefined" )
                {
                  alert('打折条件不能为空！');
                  return false;
                }
                else
                {
                //原价百分比折扣
                    if(discount_method=='rate')
                    {
                        var rate = $("input[ name='rate']").val();
                        if(!rate)
                        {
                            alert('原价折扣不能为空');
                            return false;
                        }
                    }
                //原件减去
                    if(discount_method== "reduce" )
                    {
                        var reduce = $("input[ name='reduce']").val();
                        if(!reduce)
                        {
                            alert('原价折扣不能为空');
                            return false;
                        }
                    }

                }

            }
            // 赠品
            if(promotion_method=='largess')
            {
                var largess_sum_quantity =  $("input[ name='largess_sum_quantity']").val();
                var larges_SKU =  $("input[ name='larges_SKU']").val();
                var largess_price =  $("input[ name='largess_price']").val();
                var largess_quantity =  $("input[ name='largess_quantity']").val();
                if(!largess_sum_quantity || !larges_SKU || !largess_price || !largess_quantity)
                {
                    alert('赠品内容请输入完整');
                    return false;
                }
            }
             //捆绑销售
            if(promotion_method=='bundle')
            {
                var bundleprice =  $("input[ name='bundleprice']").val();
                var bundlenum =  $("input[ name='bundlenum']").val();
                if(!bundleprice || !bundlenum )
                {
                    alert('捆绑销售内容请输入完整');
                    return false;
                }
            }
        }

    });
});