$.widget("custom.completion", {
	options: {
        column: "all"
	},
	_create: function() {
        var ownElement = this;
        var inputElement = ownElement.element;

		inputElement.addClass("ui-completion");
		inputElement.autocomplete({
			autoFocus: this.options.autoFocus,
			source: function(request, responseFunction) {
				$.getJSON("/songs/completion/", {source: ownElement.options.column, term: request.term},  function(data) {
                    responseFunction(data);
                });
			},
			minLength: 1,
			select: function(event, ui) {
				ownElement._trigger("result", ownElement, {value: ui.item.value, element: this});
			}

		});
	}
});

$(document).ready(function() {
   $(".completion").each(function(el) {
	   var classes = this.className.split(/\s+/);
	   for (var singleClassID in classes) {
		   var singleClass = classes[singleClassID];
		   if(singleClass.startsWith("completion-")) {
			   var column = singleClass.substring("completion-".length);
			   $(this).completion({column: column});
		   }
	   }
   });
});