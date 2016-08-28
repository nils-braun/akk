$.widget("custom.completion", {
	options: {
        column: "all",
        autoFocus: true
	},
	_create: function() {
        var completionObject = this;
        var completionHTMLElement = completionObject.element;

		completionHTMLElement.autocomplete({
			autoFocus: completionObject.options.autoFocus,
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
                       }, autoFocus: false
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
});

function get_audio_file_name(element) {
    return $(element).attr("data-path");
}
function add_download_binding(download_url) {
    $("#content-songlist").on("click", ".download-controls", function () {
        window.location.href = download_url + "?filename=" + get_audio_file_name(this);
        return false;
    });
}

function add_audio_binding(play_url) {
    var audio_to_play = undefined;
    var current_audio_file = undefined;

    function is_new_source(audio_file) {
        return audio_to_play == undefined || current_audio_file != audio_file;
    }

    function start_playing(audio_file_name, play_control) {
        audio_to_play = new Audio(audio_file_name);
        audio_to_play.play();

        current_audio_file = audio_file_name;

        $(play_control).addClass("playing");
    }

    function stop_playing() {
        if (audio_to_play != undefined) {
            audio_to_play.pause();
        }
        $("#content-songlist").find(".player-controls").removeClass("playing");
    }

    $("#content-songlist").on("click", ".player-controls", function () {
        var audio_file_name = play_url + "?filename=" + get_audio_file_name(this);

        stop_playing();

        if (is_new_source(audio_file_name)) {
            start_playing(audio_file_name, this);
        }

        return false;
    });
}

var currentPage = 0;
var loading = false;


function make_search_query(search_url, query, page) {
    if(loading) {
        return;
    }
    if(typeof page === "undefined") {
        $("#song-list").find("tbody").html("");
        make_search_query(search_url, query, 0);
    } else {
        loading = true;
        $.get(search_url, {query: query, page: page}, function (data) {
            if (data.length != 0) {
                $("#song-list").find("tbody").append(data);
                addBindings();
                currentPage += 1;
                loading = false;
            }
        });
    }
}

function add_endless_scroll_binding(search_url, query) {
    $("#content-wrapper").scroll(function (e) {
        var elem = $(e.currentTarget);
        if (elem[0].scrollHeight - elem.scrollTop() < elem.outerHeight() + 100) {
            make_search_query(search_url, query, currentPage);
        }
    })
}