$.widget("custom.completion", {
	options: {
        column: "all"
	},
	_create: function() {
        var completionObject = this;
        var completionHTMLElement = completionObject.element;

		completionHTMLElement.autocomplete({
			autoFocus: true,
			source: function(request, responseFunction) {
				$.getJSON("/songs/completion/", {source: completionObject.options.column, term: request.term},  function(data) {
                    responseFunction(data);
                });
			},
			minLength: 1,
			select: function(event, ui) {
				completionObject._trigger("result", completionObject, {value: ui.item.value, element: this});
			}

		});
	},

	result : function(event, item) { }
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
        var ratingObject = this;
        ratingObject.data = ratingObject.options.data;

        var length = ratingObject.options.length;
        var ratingHTMLElement = ratingObject.element;
        ratingHTMLElement.addClass("rating");

        if(ratingObject.options.changeable) {
            ratingHTMLElement.append("<input type='hidden' " +
                "name='" + ratingHTMLElement.attr("name") + "' " +
                "value='" + ratingObject.value() + "'>");
            
            ratingHTMLElement.append("<input type='button' " +
                "class='unrate-star' value=''>");
        }

        for(var i = 0; i < length; i++) {
            ratingHTMLElement.append("<span class='rating-star'></span>");
        }

        // Add handlers
        ratingObject.update(ratingObject.data);

        if (ratingObject.options.changeable) {
            var images = ratingHTMLElement.find("span");
            ratingHTMLElement.on("mouseover", "span", function () {
                ratingObject.update(images.index(this) + 1);
            });

            ratingHTMLElement.on("click", "span", function () {
                ratingObject.data = images.index(this) + 1;
                ratingObject.element.find("input[type=hidden]").val(ratingObject.data);
            });
            
            ratingHTMLElement.on("mouseover", ".unrate-star", function () {
                ratingObject.update(0);
            });

            ratingHTMLElement.on("mouseleave", ".unrate-star", function () {
                ratingObject.update(ratingObject.data);
            });
            
            ratingHTMLElement.on("click", ".unrate-star", function () {
               ratingObject.value(0);
            });

            ratingHTMLElement.on("mouseleave", function () {
                ratingObject.update(ratingObject.data);
            });
        }
	},

    update: function(number) {
        var ratingObject = this;
        var images = ratingObject.element.find("span");
        if(number > ratingObject.currentStatus) {
            images.slice(ratingObject.currentStatus, number).addClass("rating-star-filled", 1000);
        } else if(number < ratingObject.currentStatus) {
            images.slice(number, ratingObject.currentStatus).removeClass("rating-star-filled", 1000);
        }

        ratingObject.currentStatus = number;
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
               if(column == "all") {
                   $(this).completion({
                       column: column, result: function (event, item) {
                           $(this).val(item.value);
                           $("#search_form").submit();
                       }
                   });
               } else {
                   $(this).completion({column: column});
               }
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

