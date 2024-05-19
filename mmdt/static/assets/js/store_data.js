document.addEventListener("DOMContentLoaded", function () {
  const saveViaAjax = function(surveyId, questionId, payload, questionType) {
    var csrfMiddlewareToken = $('input[name="csrfmiddlewaretoken"]').val();
    $.ajax({
      type: 'POST',
      url: `/survey/surveys/${surveyId}/questions/${questionId}`,
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
    var surveyId = $("form[data-survey-id]").data('surveyId');
    const questionId = $(this).attr('name').replace('question_', '');
    const payload = $(this).val();
    saveViaAjax(surveyId, questionId, payload, 'single_option')
  });

  $('#surveyForm input[type=checkbox]').on('change', function () {
    var surveyId = $("form[data-survey-id]").data('surveyId');
    const questionId = $(this).attr('name').replace('question_', '');

    // Looks like crispy form rendered bootstrap is not properly updating multiple checkboxes with checked attribute.
    // This is a hack to set check attribute on each checkbox changes based on previous value.
    const isChecked = !!$(this).attr('checked');
    $(this).attr('checked', !isChecked);

    const payload = $(`input:checkbox[name=${$(this).attr('name')}]:checked`).map(function() {
      return Number(this.value);
    }).get();

    saveViaAjax(surveyId, questionId, payload, 'multiple_options')
  });

  $('#surveyForm input[type=text], #surveyForm textarea').on('blur', function () {
    if ($(this).val() === '') {
      return;
    }
    var surveyId = $("form[data-survey-id]").data('surveyId');
    const questionId = $(this).attr('name').replace('question_', '');
    const payload = $(this).val();
    saveViaAjax(surveyId, questionId, payload, 'text')
  });

});
