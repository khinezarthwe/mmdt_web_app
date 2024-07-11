document.addEventListener("DOMContentLoaded", function () {
  const saveViaAjax = function(surveySlug, questionId, payload, questionType) {
    var csrfMiddlewareToken = $('input[name="csrfmiddlewaretoken"]').val();
    $.ajax({
      type: 'POST',
      url: `/survey/surveys/${surveySlug}/questions/${questionId}`,
      data: {
        csrfmiddlewaretoken: csrfMiddlewareToken,
        payload: payload,
        question_type: questionType
      },
      success: function (data) {
        console.log("Question response saved successfully");
      }
    });
  }

   // save each question response in server
  $('#surveyForm input[type=radio], #surveyForm select').on('change', function () {
    var surveySlug = $("form[data-survey-slug]").data('surveySlug');
    const questionId = $(this).attr('name').replace('question_', '');
    const payload = $(this).val();
    saveViaAjax(surveySlug, questionId, payload, 'single_option')
  });

  $('#surveyForm input[type=checkbox]').on('change', function () {
    var surveySlug = $("form[data-survey-slug]").data('surveySlug');
    const questionId = $(this).attr('name').replace('question_', '');

    // Looks like crispy form rendered bootstrap is not properly updating multiple checkboxes with checked attribute.
    // This is a hack to set check attribute on each checkbox changes based on previous value.
    const isChecked = !!$(this).attr('checked');
    $(this).attr('checked', !isChecked);

    const payload = $(`input:checkbox[name=${$(this).attr('name')}]:checked`).map(function() {
      return Number(this.value);
    }).get();

    saveViaAjax(surveySlug, questionId, payload, 'multiple_options')
  });

  $('#surveyForm input[type=text], #surveyForm textarea').on('blur', function () {
    if ($(this).val() === '') {
      return;
    }
    var surveySlug = $("form[data-survey-slug]").data('surveySlug');
    const questionId = $(this).attr('name').replace('question_', '');
    const payload = $(this).val();
    saveViaAjax(surveySlug, questionId, payload, 'text')
  });

  $('#surveyForm input[type=range]').on('change', function () {
    var surveySlug = $("form[data-survey-slug]").data('surveySlug');
    const questionId = $(this).attr('name').replace('question_', '');
    const payload = $(this).val();
    saveViaAjax(surveySlug, questionId, payload, 'text')
  });

});
