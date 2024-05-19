document.addEventListener("DOMContentLoaded", function () {
  const saveViaAjax = function(surveyId, questionId, choiceId, questionType) {
    var csrfMiddlewareToken = $('input[name="csrfmiddlewaretoken"]').val();
    $.ajax({
      type: 'POST',
      url: `/survey/surveys/${surveyId}/questions/${questionId}`,
      data: {
        csrfmiddlewaretoken: csrfMiddlewareToken,
        choice_id: choiceId,
        question_type: questionType
      },
      success: function (data) {
        console.log("Question response saved successfully");
      }
    });
  }

   // save each question response in server
  $('#surveyForm input[type=radio], #surveyForm input[type=checkbox], #surveyForm select').on('change', function () {
    var surveyId = $("form[data-survey-id]").data('surveyId');
    const questionId = $(this).attr('name').replace('question_', '');
    const choiceId = $(this).val();
    saveViaAjax(surveyId, questionId, choiceId, 'single_option')
  });

  $('#surveyForm input[type=text]').on('blur', function () {
    if ($(this).val() === '') {
      return;
    }
    var surveyId = $("form[data-survey-id]").data('surveyId');
    const questionId = $(this).attr('name').replace('question_', '');
    const choiceId = $(this).val();
    saveViaAjax(surveyId, questionId, choiceId, 'text')
  });

});
