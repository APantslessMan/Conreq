let modal_dialog = $("#modal-dialog");
let modal_loaded = false;

// Fetches a modal via AJAX
var generate_modal = function (modal_url) {
	// Fetch the series modal
	modal_loaded = false;
	get_url(modal_url, function (modal_html) {
		// Save that the modal was successfully loaded
		modal_loaded = true;

		// Place the new HTML on the page
		modal_dialog[0].innerHTML = DOMPurify.sanitize(modal_html);

		// Show the new content
		$("#modal-container .loading-animation").hide();
		$("#modal-content").show();
		$("#modal-container").modal("show");

		// Add click events
		request_click_event();
		series_modal_click_event();
		modal_select_all_click_event();
		modal_expand_click_event();
		row_title_click_event();
		row_checkbox_click_event();
		row_suboption_title_click_event();
		row_suboption_checkbox_click_event();
		report_modal_click_event();
		report_click_event();
		report_selection_modal_click_event();
	}).fail(function () {
		// Server couldn't fetch the modal
		conreq_no_response_toast_message();
		$("#modal-container").modal("hide");
	});

	// If the modal is taking too long to load, show a loading animation
	setTimeout(function () {
		if (!modal_loaded) {
			// Show the loading icon
			$("#modal-content").hide();
			$("#modal-container").modal("show");
			$("#modal-container .loading-animation").show();
		}
	}, 300);
};
