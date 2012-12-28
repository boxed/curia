/*
calendar.js - Calendar functions by Adrian Holovaty
*/

function removeChildren(a) { // "a" is reference to an object
    while (a.hasChildNodes()) a.removeChild(a.lastChild);
}

// quickElement(tagType, parentReference, textInChildNode, [, attribute, attributeValue ...]);
function quickElement() {
    var obj = document.createElement(arguments[0]);
    if (arguments[2] != '' && arguments[2] != null) {
        var textNode = document.createTextNode(arguments[2]);
        obj.appendChild(textNode);
    }
    var len = arguments.length;
    for (var i = 3; i < len; i += 2) {
        obj.setAttribute(arguments[i], arguments[i+1]);
    }
    arguments[1].appendChild(obj);
    return obj;
}

function isLeapYear(year) {
    return (((year % 4)==0) && ((year % 100)!=0) || ((year % 400)==0));
}
function getDaysInMonthOfYear(month,year) {
    var days;
    if (month==1 || month==3 || month==5 || month==7 || month==8 || month==10 || month==12) {
        days = 31;
    }
    else if (month==4 || month==6 || month==9 || month==11) {
        days = 30;
    }
    else if (month==2 && isLeapYear(year)) {
        days = 29;
    }
    else {
        days = 28;
    }
    return days;
}

// Calendar -- A calendar instance
function Calendar(div_id, get_data) {
    // div_id (string) is the ID of the element in which the calendar will
    //     be displayed
    // clickCallback (string) is the name of a JavaScript function that will be
    //     called with the parameters (year, month, day) when a day in the
    //     calendar is clicked
    this.div_id = div_id;
    this.putDataCallback = get_data;
    this.today = new Date();
    this.currentMonth = this.today.getMonth() + 1;
    this.currentYear = this.today.getFullYear();
}
Calendar.prototype = {
    monthsOfYear: gettext('January February March April May June July August September October November December').split(' '),
    shortDaysOfWeek: gettext('S M T W T F S').split(' '),
    daysOfWeek: gettext('Sunday Monday Tuesday Wednesday Thursday Friday Saturday').split(' '),
    startOfWeek: 1,

    drawDate: function(month, year) {
        this.currentMonth = month;
        this.currentYear = year;
        this.drawCurrent();
    },
    drawPreviousMonth: function() {
        if (this.currentMonth == 1) {
            this.currentMonth = 12;
            this.currentYear--;
        }
        else {
            this.currentMonth--;
        }
        this.drawCurrent();
    },
    drawNextMonth: function() {
        if (this.currentMonth == 12) {
            this.currentMonth = 1;
            this.currentYear++;
        }
        else {
            this.currentMonth++;
        }
        this.drawCurrent();
    },
    drawPreviousYear: function() {
        this.currentYear--;
        this.drawCurrent();
    },
    drawNextYear: function() {
        this.currentYear++;
        this.drawCurrent();
    },
    drawToday: function()
	{
		this.currentMonth = this.today.getMonth() + 1;
	    this.currentYear = this.today.getFullYear();
		this.drawCurrent();
	},
	
    drawDayOfWeekHeader: function() {
        var tableRow = quickElement('tr', this.tableBody, '', 'class', 'day_of_week');
        for (var i = this.startOfWeek; i < 7+this.startOfWeek; i++) {
            quickElement('th', tableRow, this.daysOfWeek[i%7]);
        }
        return tableRow;
    },
    drawDay: function(tableRow, i, year, month, day, css_classes) {
        if (i%7 == 0 && day != 1) {
            tableRow = quickElement('tr', this.tableBody);
        }
        if (this.today.getFullYear() == year && this.today.getMonth()+1 == month && this.today.getDate() == day)
            css_classes += ' today';
        var cell = quickElement('td', tableRow, ' ', 'class', css_classes);
        div = quickElement('div', cell, day, 'class', 'date');
        if (this.putDataCallback) {
            cell.year = year;
            cell.month = month;
            cell.date = day;
            this.putDataCallback(cell);
        }
        return tableRow;
    },
    drawCurrent: function() { // month = 1-12, year = 1-9999
        var month = parseInt(this.currentMonth);
        var year = parseInt(this.currentYear);
        var calDiv = document.getElementById(this.div_id);
        removeChildren(calDiv);
        var calTable = document.createElement('table');
        caption = quickElement('caption', calTable);
        caption.innerHTML = '<a href="#" onClick="foo.drawPreviousYear();">&lt;</a> '+year + ' <a href="#" onClick="foo.drawNextYear();">&gt;</a><br />' +
            '<a href="#" onClick="foo.drawPreviousMonth();">&lt;</a> ' + this.monthsOfYear[month-1] + ' <a href="#" onClick="foo.drawNextMonth();">&gt;</a>';
        this.tableBody = quickElement('tbody', calTable);

        var startingPos = new Date(year, month-1, 1).getDay()-this.startOfWeek;
        var days = getDaysInMonthOfYear(month, year);
        if (startingPos < 0) {
            startingPos = 7+startingPos;
        }

        this.drawDayOfWeekHeader(this.tableBody);
        
        // Draw blanks before first of month
        var currentMonth = month == 1? 12: month-1;
        var currentYear = month == 1? year-1: year;
        var currentDay = getDaysInMonthOfYear(currentMonth, currentYear)-startingPos+1;
        tableRow = quickElement('tr', this.tableBody);
        for (var i = 0; i < startingPos; i++) {
           tableRow = this.drawDay(tableRow, i, currentYear, currentMonth, currentDay++, 'day overflow') 
        }

        // Draw days of month
        var currentDay = 1;
        for (var i = startingPos; currentDay <= days; i++) {
           tableRow = this.drawDay(tableRow, i, year, month, currentDay++, 'day')
        }

        // Draw blanks after end of month
        currentDay = 1;
        while (tableRow.childNodes.length < 7) {
            tableRow = this.drawDay(tableRow, i, month == 12? year+1: year, month == 12? 1: month+1, currentDay++, 'day overflow')
        }

        calDiv.appendChild(calTable);
    }
}
