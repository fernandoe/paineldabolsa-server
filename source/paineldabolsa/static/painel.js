$(function() { 

    $(".gridster ul").gridster({
        widget_margins : [ 1, 1 ],
        widget_base_dimensions : [ 70, 50 ],
        max_cols : 10,
        min_cols : 10
    });

    $("li").click(function() {

        var codigo = this.childNodes[1].innerText;
        $('#myModalLabel').text(codigo);

        var modal = $('#myModal'), modalBody = $('#myModal .modal-body');
        $("#grafico").attr("src", "/paineldabolsa/grafico/" + codigo + "/");

        $('#myModal').modal('show');
    });

});

