// Create the chart for user statistics
const ctx = document.getElementById('usersChart').getContext('2d');
const usersChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ user_statistics.month_labels | safe }},
datasets: [{
    label: 'User Count',
    data: {{ user_statistics.user_counts | safe }},
    backgroundColor: 'rgba(54, 162, 235, 0.2)',
    borderColor: 'rgba(54, 162, 235, 1)',
    borderWidth: 1,
        }, {
    label: 'User Count Line',
    data: {{ user_statistics.user_counts | safe }},
    type: 'line',
    fill: false,
    borderColor: 'rgba(255, 99, 132, 1)',
    pointRadius: 5,
    yAxisID: 'y2',
        }]
    },
options: {
    responsive: false,
        scales: {
        y: {
            beginAtZero: true,
                ticks: {
                stepSize: 1,
                    suggestedMin: 1,
                        suggestedMax: 100,
                },
            title: {
                display: true,
                    text: 'User Count (Bar)'
            }
        },
        y2: {
            beginAtZero: true,
                ticks: {
                stepSize: 1,
                    suggestedMin: 1,
                        suggestedMax: 100,
                },
            position: 'right',
                grid: {
                display: false,
                },
            title: {
                display: true,
                    text: 'User Count (Line)'
            }
        }
    }
}
});

// Assuming 'commodity_statistics' is available in your template
const commodityStatistics = {{ commodity_statistics| safe }};
console.log("Knowledge Labels:", {{ knowledge_labels| safe }});

// Extracting commodity names and tagged counts
const commodityNames = commodityStatistics.tagged_counts.map(entry => entry.commodity_name);
const taggedCounts = commodityStatistics.tagged_counts.map(entry => entry.total_tags);

// Now you can use commodityNames and taggedCounts in your chart creation
const pie = document.getElementById('taggedCommoditiesChart').getContext('2d');
const taggedCommoditiesChart = new Chart(pie, {
    type: 'pie',
    data: {
        labels: commodityNames,
        datasets: [{
            data: taggedCounts,
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)',
                'rgba(153, 102, 255, 0.2)',
                'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1,
        }]
    },
    options: {
        responsive: false,
        plugins: {
            datalabels: {
                display: true,
                formatter: (value, context) => {
                    const commodityName = context.chart.data.labels[context.dataIndex];
                    const tagPercentage = tagPercentages[context.dataIndex];
                    return `${commodityName}: ${value} (Tag Percentage: ${tagPercentage}%)`;
                },
                color: '#fff',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                borderRadius: 4,
                anchor: 'end',
                align: 'end',
            }
        }
    }
});


// Assuming 'search_terms', 'frequencies', 'filtered_commodity_names', and 'filtered_commodity_frequencies' are available in your template
const searchTerms = {{ search_terms| safe }};
const frequencies = {{ frequencies| safe }};
const filteredCommodityNames = {{ filtered_commodity_names| safe }};
const filteredCommodityFrequencies = {{ filtered_commodity_frequencies| safe }};
const capitalizedSearchTerms = searchTerms.map(name => name.charAt(0).toUpperCase() + name.slice(1));

// Get the canvas context
const lines = document.getElementById('searchTermChart').getContext('2d');

// Create the line chart
const searchTermChart = new Chart(lines, {
    type: 'line',
    data: {
        labels: capitalizedSearchTerms, // Use the array of unique terms
        datasets: [
            {
                label: 'Search Term Frequencies',
                data: frequencies, // Use the full frequencies array
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                fill: true // Handle missing values at the end
            },
        ]
    },
    options: {
        responsive: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Frequency'
                },
                ticks: {
                    stepSize: 1, // Force ticks to be integers
                    precision: 0 // Ensure that there are no decimal points
                }
            },
            x: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: ' Search Terms'
                }
            }
        }
    }
});


// Assuming 'daily_labels' and 'daily_discussion_counts' are available in your template
const dailyLabels = {{ daily_labels| safe }};
const dailyDiscussionCounts = {{ daily_discussion_counts| safe }};

// Parse the discussion counts as integers
const parsedDiscussionCounts = dailyDiscussionCounts.map(function (count) {
    return parseInt(count, 10); // This will parse the count as an integer
});

// Get the canvas context
const barChart = document.getElementById('postsChart').getContext('2d');

// Create the bar chart
const postsChart = new Chart(barChart, {
    type: 'bar',
    data: {
        labels: dailyLabels,
        datasets: [{
            label: 'Daily Discussion Counts',
            data: parsedDiscussionCounts,
            backgroundColor: 'rgba(75, 192, 192, 0.7)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: false,
        scales: {
            y: {
                type: 'linear', // Set type to linear for integer values
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Total Discussions'
                },
                ticks: {
                    stepSize: 1, // Force ticks to be integers
                    precision: 0, // Ensure that there are no decimal points
                }
            },
            x: {  // Change x to xAxis
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Day'
                }
            }
        }
    }
});