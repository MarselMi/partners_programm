var hours_stat_today = document.getElementById('hours_stat_today').textContent;
var new_stat_today = hours_stat_today.substring(1, hours_stat_today.length - 1).split(', ').map(Number);

var hours_stat_yesterday = document.getElementById('hours_stat_yesterday').textContent;
var new_stat_yesterday = hours_stat_yesterday.substring(1, hours_stat_yesterday.length - 1).split(', ').map(Number);

var options = {
    series: [{
        name: 'Сегодня',
        data: (new_stat_today)
    }, {
        name: 'Вчера',
        data: (new_stat_yesterday)
    }],
    chart: {
        type: 'bar',
        height: 270
    },
    grid: {
        borderColor: '#f2f6f7',
    },
    colors: ["#0d6efd", "#CCD7E8"],
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '55%',
            endingShape: 'rounded'
        },
    },
    dataLabels: {
        enabled: false
    },
    stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
    },
    xaxis: {
        categories: ['00', '01', '02', '03', '04', '05', '06',
            '07', '08', '09', '10', '11', '12', '13', '14', '15', '16',
            '17', '18', '19', '20', '21', '22', '23'],
    },
    yaxis: {
        title: {
            text: 'Активации',
            style: {
                color: '#adb5be',
                fontSize: '14px',
                fontFamily: 'Nunito Sans, sans-serif',
                fontWeight: 400,
                cssClass: 'apexcharts-yaxis-label',
            },
        }
    },
    legend: {
        show: true,
        position: 'top',
    },
    fill: {
        opacity: 1
    },
    tooltip: {
        y: {
            formatter: function (val) {
                return val
            }
        }
    }
};

var chart = new ApexCharts(document.querySelector("#statistics1"), options);
chart.render();


// Project Budget chart //
function statistics1dis() {
    setTimeout(() => {
        var options1 = {
            series: [{
                name: 'Total Orders',
                data: [44, 42, 57, 86, 58, 55, 70, 43, 23, 54, 77, 34],
            }, {
                name: 'Total Sales',
                data: [34, 22, 37, 56, 21, 35, 60, 34, 56, 78, 89, 53],
            }],
            chart: {
                type: 'bar',
                height: 280
            },
            grid: {
                borderColor: '#f2f6f7',
            },
            colors: [myVarVal || "#38cab3", "#e4e7ed"],
            plotOptions: {
                bar: {
                    colors: {
                        ranges: [{
                            from: -100,
                            to: -46,
                            color: '#ebeff5'
                        }, {
                            from: -45,
                            to: 0,
                            color: '#ebeff5'
                        }]
                    },
                    columnWidth: '40%',
                }
            },
            dataLabels: {
                enabled: false,
            },
            stroke: {
                show: true,
                width: 4,
                colors: ['transparent']
            },
            legend: {
                show: true,
                position: 'top',
            },
            yaxis: {
                title: {
                    text: 'Growth',
                    style: {
                        color: '#adb5be',
                        fontSize: '14px',
                        fontFamily: 'Nunito Sans, sans-serif',
                        fontWeight: 600,
                        cssClass: 'apexcharts-yaxis-label',
                    },
                },
                labels: {
                    formatter: function (y) {
                        return y.toFixed(0) + "";
                    }
                }
            },
            xaxis: {
                type: 'month',
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'sep', 'oct', 'nov', 'dec'],
                axisBorder: {
                    show: true,
                    color: 'rgba(119, 119, 142, 0.05)',
                    offsetX: 0,
                    offsetY: 0,
                },
                axisTicks: {
                    show: true,
                    borderType: 'solid',
                    color: 'rgba(119, 119, 142, 0.05)',
                    width: 6,
                    offsetX: 0,
                    offsetY: 0
                },
                labels: {
                    rotate: -90
                }
            }
        };
        document.getElementById('statistics1').innerHTML = '';
        var chart1 = new ApexCharts(document.querySelector("#statistics1"), options1);
        chart1.render();
    }, 300);
}