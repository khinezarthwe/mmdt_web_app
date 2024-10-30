document.addEventListener('DOMContentLoaded', function () {
    allQuestionsData.forEach(function(questionData) {
        var ctx = document.getElementById('resultChart_' + questionData.id).getContext('2d');

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: questionData.resultsData.labels,
                datasets: [{
                    data: questionData.resultsData.data,
                    backgroundColor: [
                        '#f2c11d',
                        '#003399',
                        '#467df2',
                        '#ff6384',
                        '#db0718',
                        '#ffce56',
                        '#4bc0c0',
                        '#9966cc',
                        '#ff9900',
                        '#669900',
                    ],
                    borderColor: [
                        '#f2c11d',
                        '#003399',
                        '#467df2',
                        '#ff6384',
                        '#db0718',
                        '#ffce56',
                        '#4bc0c0',
                        '#9966cc',
                        '#ff9900',
                        '#669900',
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: false,
                aspectRatio: 1, 
            }
        });
    });
});
