document.addEventListener("DOMContentLoaded", function () {
   // save each question response in server
  $('#surveyForm input[type=radio], #surveyForm input[type=checkbox], #surveyForm select').on('change', function () {
    var surveyId = $("form[data-survey-id]").data('surveyId');
    var csrfMiddlewareToken = $('input[name="csrfmiddlewaretoken"]').val();
    const questionId = $(this).attr('name').replace('question_', '');
    const choiceId = $(this).val();
    $.ajax({
      type: 'POST',
      url: `/survey/surveys/${surveyId}/questions/${questionId}`,
      data: {
        csrfmiddlewaretoken: csrfMiddlewareToken,
        choice_id: choiceId
      },
      success: function (data) {
        console.log("Question response saved successfully");
      }
    });
  });

  $('#surveyForm input[type=text]').on('blur', function () {
    if ($(this).val() === '') {
      return;
    }
    var surveyId = $("form[data-survey-id]").data('surveyId');
    var csrfMiddlewareToken = $('input[name="csrfmiddlewaretoken"]').val();
    const questionId = $(this).attr('name').replace('question_', '');
    const choiceId = $(this).val();
    $.ajax({
      type: 'POST',
      url: `/survey/surveys/${surveyId}/questions/${questionId}`,
      data: {
        csrfmiddlewaretoken: csrfMiddlewareToken,
        choice_id: choiceId,
        is_text: true
      },
      success: function (reponseCode) {
        if (reponseCode === 200) {
          console.log("Question response saved successfully");
        } else {
          console.log("Question response not saved successfully. Error code: " + reponseCode);
        }
      }
    });
  });

});
