document.addEventListener('DOMContentLoaded', function () {
    // Add event listener for tab change
    $('#questionTabs a').on('click', function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    // Update URL hash on tab change
    $('#questionTabs a').on('shown.bs.tab', function (e) {
        var tabId = e.target.getAttribute('id');
        window.location.hash = tabId;
    });

    // Activate tab based on URL hash
    var hash = window.location.hash;
    if (hash) {
        $('#questionTabs a[href="' + hash + '"]').tab('show');
    }
});
