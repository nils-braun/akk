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

$.widget("custom.rating", {
    options: {
        length: 5,
        data: 0,
        changeable: true
    },

    currentStatus: 0,
    data: 0,

	_create: function() {
        var ownElement = this;
        ownElement.data = ownElement.options.data;

        // Add images
        var length = ownElement.options.length;
        var inputElement = ownElement.element; //.element.find("div");
        inputElement.addClass("rating");


        if(ownElement.options.changeable) {
            inputElement.append("<input type='hidden' name='" + inputElement.attr("name") + "' value='" + ownElement.value() + "'>");
            inputElement.append("<input type='button' " +
                "class='unrate-star' value='' " +
                "onclick='$(this).parent().rating(\"value\", 0);'>");
        }

        for(var i = 0; i < length; i++) {
            inputElement.append("<span class='rating-star'></span>");
        }

        // Add handlers
        ownElement.update(ownElement.data);

        if (ownElement.options.changeable) {
            var images = inputElement.find("span");
            inputElement.on("mouseover", "span", function () {
                ownElement.update(images.index(this) + 1);
            });

            inputElement.on("mouseover", ".unrate-star", function () {
                ownElement.update(0);
            });

            inputElement.on("mouseleave", ".unrate-star", function () {
                ownElement.update(ownElement.data);
            });

            inputElement.on("click", "span", function () {
                ownElement.data = images.index(this) + 1;
                ownElement.element.find("input[type=hidden]").val(ownElement.data);
            });

            inputElement.on("mouseleave", function () {
                ownElement.update(ownElement.data);
            });
        }
	},

    update: function(number) {
        var ownElement = this;
        var images = ownElement.element.find("span");
        if(number > ownElement.currentStatus) {
            images.slice(ownElement.currentStatus, number).addClass("rating-star-filled", 1000);
        } else if(number < ownElement.currentStatus) {
            images.slice(number, ownElement.currentStatus).removeClass("rating-star-filled", 1000);
        }

        ownElement.currentStatus = number;
    },

    reset: function() {
        this.data = 0;
        this.update(0);
    },

    value: function(value) {
        if (value == undefined) {
            return this.currentStatus;
        } else {
            this.data = value;
            this.update(value);
        }
    }
});


function addBindings() {
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

    $(".rating").each(function(el) {
        $(this).rating({data: $(this).attr("data-value"),
                        changeable: typeof $(this).attr("data-enabled") !== typeof undefined});
    });
}

$(document).ready(function() {
    addBindings();
    $("#content-wrapper").bind("DOMNodeInserted", function() {
        addBindings();
    });
});

