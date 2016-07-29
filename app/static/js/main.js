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
		inputElement.keypress(function(event) {
			if(event.keyCode == 13) {
				$(this).autocomplete("close");
				$(".ui-complete").hide();
				ownElement._trigger("result", ownElement, {value: ownElement.value(), element: this});
			}
		});
	}
});

$(document).ready(function() {
   $(".input").completion();
});