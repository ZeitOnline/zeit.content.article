(function($) {

zeit.cms.declare_namespace('zeit.content.article');

zeit.content.article.normalize_filename = function(filename) {
    var result = filename;
    result = result.trim().toLowerCase();
    result = result.replace('ä', 'ae');
    result = result.replace('ö', 'oe');
    result = result.replace('ü', 'ue');
    result = result.replace('ß', 'ss');
    result = result.replace(/[^a-z0-9]/g, '-');
    result = result.replace(/-+/g, '-');
    return result;
};


$(document).bind('fragment-ready', function(event) {
    $('#new-filename\\.rename_to', event.__target).bind('change', function() {
        var input = $(this);
        input.val(zeit.content.article.normalize_filename(input.val()));
    });
});


$(document).ready(function() {
    $('.breakingnews-title').bind('keyup', function() {
        var title = $(this).val();
        var target = '#form\\.__name__';
        $(target).val(title);
        $(target).trigger('change');
    });

    $('#form\\.__name__').bind('change', function() {
        var input = $(this);
        input.val(zeit.content.article.normalize_filename(input.val()));
    })
});


}(jQuery));
