/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, onRendered, useState } = owl
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { loadJS } from "@web/core/assets";
import { useRef } from "@odoo/owl";
// import { Modal } from "@dev_attendance_dashboard_advanced/Modal";

export class AttendanceDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.rpc = this.env.services.rpc;
        this.state = useState({
            employee_list: { value: [{}] },
            leave_summary : {},
            days: { value: 0 },
            user_name: { value: 'User Image' },
            user_img: { value: 'User Name' },
            requestData : {},
            rowsPerPage : 10,
            currentPage : 1,
            all_employee_data : [],
            all_present : [],
            all_absent : [],
            on_leave : [],
            late_checkin : [],
            // Contadores para el día actual
            all_present_today : [],
            all_absent_today : [],
            on_leave_today : [],
            late_checkin_today : [],

        })

                       
        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    

    async onWillStart() {
        await this.getCardData()
        await this.getUserDetail()
        await this.getGreetings()
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js")
        
    }

    async onMounted() {
        await this.renderAttendanceDashboardFilter();
        await this.getAttendanceData();
        this.getLeaveDetail({}, this.state.rowsPerPage, this.state.currentPage)
        document.querySelector('#excel_download_btn')?.addEventListener('click', () => this._downloadExcelReport());
        document.querySelector('#pdf_download_btn')?.addEventListener('click', () => this._printReport());
        document.querySelector('#send_email_btn')?.addEventListener('click', () => this._sendEmailReport());
    }

    getUserDetail() {
        var self = this;
        rpc('/attn/user_detail').then(function (response) {
            self.state.user_name.value = response['user_name']
            self.state.user_img.value = response['user_img']
        });
    }

    getAttendanceData(requestData) {
        var self = this;
        const data = [];
        var request = {}
        if (requestData) {
            request = requestData;
            console.log(request);
        }
        rpc('/employee/attendance', { 'request': request }).then(function (response) {
            self.state.employee_list.value = response[0]
            self.state.days.value = response[1].days
            self.prepareRoomCalender()
        })
        
    }

    getDayName(day, month, year) {
        console.log("called");
        const days = [_t('Sun'), _t('Mon'), _t('Tue'), _t('Wed'), _t('Thu'), _t('Fri'), _t('Sat')];
        const date = new Date(parseInt(year), parseInt(month), day);
        const dayIndex = date.getDay();
        const dayName = days[dayIndex];
        return dayName
    }

    // Métodos para traducciones de la leyenda del calendario
    getLegendP() {
        return _t('P:');
    }

    getLegendPresent() {
        return _t('Present');
    }

    getLegendA() {
        return _t('A:');
    }

    getLegendAbsent() {
        return _t('Absent');
    }

    getLegendL() {
        return _t('L:');
    }

    getLegendLeave() {
        return _t('Leave');
    }

    getLegendH() {
        return _t('H:');
    }

    getLegendHoliday() {
        return _t('Holiday');
    }

    getLegendMD() {
        return _t('MD:');
    }

    getLegendMinorDelay() {
        return _t('Minor Delay');
    }

    getLegendUA() {
        return _t('UA:');
    }

    getLegendUnjustifiedAbsence() {
        return _t('Unjustified Absence');
    }

    _downloadExcelReport() {
        const filter = this.state.requestData;
        const query = new URLSearchParams(filter).toString();
        window.open('/attendance/report/download?' + query, '_blank');
    }

    _printReport() {
        const attendanceId = this.state.selectedAttendanceId; // set this when a record is selected
        if (!attendanceId) {
            alert(_t("Please select an employee first."));
            return;
        }
        const url = `/dashboard/attendance/${attendanceId}?report_type=pdf`;
        window.open(url, '_blank');
    }

    _sendEmailReport() {
        const filters = this.state.requestData;  // contains department, employee, year, month filters
        const self = this;
        rpc('/send_attendance_email', {
            data: {},  
            ...filters  
        }).then(response => {
            
            if (response.success) {
                self.notification.add(_t("Attendance report sent successfully."), {
                    type: "success",
                });
            } else {
                self.notification.add(_t("Failed to send attendance report. ") + (response.message || _t("Unknown error occurred.")), {
                    type: "danger",
                });
            }
        }).catch(error => {
            self.notification.add(_t("Something went wrong, while sending email."), {
                type: "danger",
            });
        });
    }
    
      
    action_all_employees(e) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var rec_id = e.currentTarget.getAttribute('rec-id');
        var action = e.currentTarget.id || false;
        var title_name = ' ';
        var domain = false;
        if (action == 'all_employee_data1')
        {
            domain = [["id", "in", this.state.all_employee_data]];
            title_name = _t('All Employees')
        }
        else if (action == 'all_present1')
        {
            domain = [["id", "in", this.state.all_present_today]];
            title_name = _t('Total Present (Today)')
        }
        else if (action == 'all_absent1')
        {
            domain = [["id", "in", this.state.all_absent_today]];
            title_name = _t('Total Absent (Today)')
        }
        else if (action == 'on_leave1')
        {
            domain = [["id", "in", this.state.on_leave_today]];
            title_name = _t('On Leave (Today)')
        }
        else if (action == 'late_checkin1')
        {
            domain = [["id", "in", this.state.late_checkin_today]];
            title_name = _t('Late CheckIn (Today)')
        }
        
        else if (rec_id != 'undefined') {
            domain = [["id", "=", rec_id]]
        }
        this.action.doAction({
            name: title_name,
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            domain: domain,
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options)
    }

    async getCardData(){
        var self = this;
            const result = await rpc('/get/attendance/tiles/data');
            self.state.all_employee_data=result['all_employee_data']
            self.state.all_present=result['all_present']
            self.state.all_absent=result['all_absent']
            self.state.on_leave=result['on_leave']
            self.state.late_checkin=result['late_checkin']
            // Contadores para el día actual
            self.state.all_present_today=result['all_present_today'] || []
            self.state.all_absent_today=result['all_absent_today'] || []
            self.state.on_leave_today=result['on_leave_today'] || []
            self.state.late_checkin_today=result['late_checkin_today'] || []
            
        return result;
    }

    getInitials(name) {
        return name
          ? name
              .split(" ")
              .map((word) => word.charAt(0).toUpperCase())
              .join("")
              .slice(0, 2)
          : "";
      }
      

    async prepareRoomCalender() {
        // creating header 
        var self = this;
        var thead = document.querySelector("#attendanceCalender thead");
        var monthSelect = document.querySelector("#month_selection");
        var yearSelect = document.querySelector('#year_selection');
        
        // Verificar que los elementos existan antes de continuar
        if (!thead || !monthSelect || !yearSelect) {
            console.warn("Elementos del calendario no encontrados. El componente puede haber sido desmontado.");
            return;
        }
        
        thead.innerHTML = ' ';
        var tr = document.createElement('tr')
        var month = monthSelect.value
        var year = yearSelect.value

        
        var days = self.state.days.value
        const employee_data = this.state.employee_list.value

        for (var i = 0; i <= days + 6; i++) {
            let th = document.createElement('th')
            if (i == 0) {
                th.style = "width:100px; min-width:100px; max-width:100px; background: #E0dfdf; border:1px solid #525252; text-align:center;  position: sticky; top: 0; z-index: 1;"
                th.textContent = _t("Employees")
            } else if (i == days + 1) {
                th.style = "background: #e2ebb9; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0; z-index: 1;"
                th.innerHTML = "&nbsp;" + _t("P") + "&nbsp;";
            } else if (i == days + 2) {
                th.style = "background: #ffc9c4; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0; z-index: 1;"
                th.innerHTML = "&nbsp;" + _t("A") + "&nbsp;";
            } else if (i == days + 3) {
                th.style = "background: #ffe4b8; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0; z-index: 1;"
                th.innerHTML = "&nbsp;" + _t("L") + "&nbsp;";
            } else if (i == days + 4) {
                th.style = "background:#bfd2ff; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0;z-index: 1;"
                th.innerHTML = "&nbsp;" + _t("H") + "&nbsp;";
            } else if (i == days + 5) {
                th.style = "background:#ffeb3b; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0;z-index: 1;"
                th.innerHTML = "&nbsp;" + _t("RL") + "&nbsp;";
            } else if (i == days + 6) {
                th.style = "background:#ff9800; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0;z-index: 1;"
                th.innerHTML = "&nbsp;" + _t("UA") + "&nbsp;";
            } else {
                var day = this.getDayName(i, month, year)
                th.style = "background: #Eeeeee; height:35px; border:1px solid #525252; text-align:center;  position: sticky; top: 0;z-index: 1;"
                th.innerHTML = day + "<br>" + i;
            }
            tr.appendChild(th)
        }
        thead.appendChild(tr)

        // console.log(this.state.employee_list.value);

        // creating rows of table body
        var tbody = document.querySelector("#attendanceCalender tbody");
        if (!tbody) {
            console.warn("Tbody del calendario no encontrado. El componente puede haber sido desmontado.");
            return;
        }
        tbody.innerHTML = ' ';

        // Variables para calcular los totales
        var total_p = 0;
        var total_a = 0;
        var total_l = 0;
        var total_h = 0;
        var total_md = 0;
        var total_ua = 0;

        for (var i = 0; i < employee_data.length; i++) {
            var tr = document.createElement('tr');
            tr.style = "height:50px;";
            for (var j = 0; j <= days + 6; j++) {
                var td = document.createElement('td');
                if (j === 0) {
                    td.style = "width:100px; min-width:100px; max-width:100px; border:1px solid #525252; padding:5px; text-align:center;";
                    if (employee_data[i]) {
                        var employee = employee_data[i];
                        // ${employee_data[i].img}
                        var emp = `<div class="d-flex flex-column align-items-center" style="gap: 8px;"> 
                                    `
                        if (employee_data[i].img) {
                            console.log(employee_data[i].img);
                            
                            emp += `<img src="data:image/png;base64,${employee_data[i].img}" class="emp-img" alt="${employee_data[i].name} (Image)" style="flex-shrink: 0;" />`
                        } else {
                            emp += `<img src="/dev_attendance_dashboard_advanced/static/src/image/emp.png" class="emp-img" style="flex-shrink: 0;" />`
                            // const initials = employee_data[i].name.split(" ").map((word) => word.charAt(0).toUpperCase()).join("").slice(0, 2)


                            
                            // emp += `
                            //   <div class="emp-initials">
                            //     ${initials}
                            //   </div>`;
                        }

                        emp += ` </div> 
                                    <div class="col-9 d-flex align-items-center"> 
                                        <div class="col" style="font-weight:600;">${employee_data[i].name}</div>
                                    </div> 
                                </div>`

                        td.innerHTML = emp;
                        (function (employee) {
                            td.addEventListener("click", function () {
                                self.action.doAction({
                                    name: _t("Employee"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'hr.employee',
                                    domain: [["id", "in", [employee.id]]],
                                    view_mode: 'list,form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    target: 'current'
                                });
                            });
                        })(employee); // Pass room data to the IIFE
                    } else {
                        td.textContent = "-";
                    }
                    tr.appendChild(td);

                } else if (j === days + 1) {
                    var p_value = employee_data[i].summary['p'] || 0;
                    total_p += parseInt(p_value) || 0;
                    td.style = "text-align:center; background-color:#e2ebb9; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                    td.textContent = p_value;
                    tr.appendChild(td);
                    if (employee.all_present) {
                        (function (employee) {
                            td.addEventListener("click", function () {
                                self.action.doAction({
                                    name: _t("Attendance"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'hr.attendance',
                                    domain: [["id", "in", employee.all_present]],
                                    view_mode: 'list,form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    target: 'new'
                                });
                            });
                        })(employee);
                    }
                } else if (j == days + 2) {
                    var a_value = employee_data[i].summary['a'] || 0;
                    total_a += parseInt(a_value) || 0;
                    td.style = "text-align:center; background-color:#ffc9c4; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                    td.textContent = a_value;
                    tr.appendChild(td);
                } else if (j == days + 3) {
                    var l_value = employee_data[i].summary['l'] || 0;
                    total_l += parseInt(l_value) || 0;
                    td.style = "text-align:center; background-color:#ffe4b8; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                    td.textContent = l_value;
                    tr.appendChild(td);
                    var employee = employee_data[i];
                    if (employee.all_leave) {
                        (function (employee) {
                            td.addEventListener("click", function () {
                                self.action.doAction({
                                    name: _t("Leaves"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'hr.leave',
                                    domain: [["id", "in", employee.all_leave]],
                                    view_mode: 'list,form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    target: 'new'
                                });
                            });
                        })(employee);
                    }
                } else if (j == days + 4) {
                    var h_value = employee_data[i].summary['h'] || 0;
                    total_h += parseInt(h_value) || 0;
                    td.style = "text-align:center; background-color:#bfd2ff; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                    td.textContent = h_value;
                    tr.appendChild(td);
                    var employee = employee_data[i];
                    if (employee.all_holidays) {
                        (function (employee) {
                            td.addEventListener("click", function () {
                                self.action.doAction({
                                    name: _t("Holidays"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'resource.calendar.leaves',
                                    domain: [["id", "in", employee.all_holidays]],
                                    view_mode: 'list,form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    target: 'new'
                                });
                            });
                        })(employee);
                    }
                } else if (j == days + 5) {
                    var md_value = parseInt(employee_data[i].summary['md']) || 0;
                    total_md += md_value;
                    td.style = "text-align:center; background-color:#ffeb3b; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                    td.textContent = md_value;
                    tr.appendChild(td);
                } else if (j == days + 6) {
                    var ua_value = parseInt(employee_data[i].summary['ua']) || 0;
                    total_ua += ua_value;
                    td.style = "text-align:center; background-color:#ff9800; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                    td.textContent = ua_value;
                    tr.appendChild(td);
                }
                else {
                    if (employee_data[i].attendance) {
                        var attendance = employee_data[i].attendance
                        var employee = employee_data[i]
                        if (attendance[j].status === 'absent') {
                            td.style = "text-align:center; font-weight:600; font-size:15px; border-bottom:1px #525252 solid;";
                            td.textContent = "A"
                        } else if (attendance[j].status == 'W') {
                            td.style = "text-align:center; font-weight:600; background-color: #Eeeeee; font-size:15px; border-bottom:1px #525252 solid;";
                            td.textContent = "W"
                        } else if (attendance[j].status === 'l') {
                            td.style = "text-align:center; font-weight:600; color:red; font-size:15px; border-bottom:1px #525252 solid;";
                            td.textContent =  attendance[j].hours;
                            var day_attn = attendance[j];
                            (function (day_attn) {
                                td.addEventListener("click", function () {
                                    self.action.doAction({
                                        name: _t("Leave"),
                                        type: 'ir.actions.act_window',
                                        res_model: 'hr.leave',
                                        domain: [["id", "in", [day_attn.ids]]],
                                        view_mode: 'list,form',
                                        views: [
                                            [false, 'list'],
                                            [false, 'form']
                                        ],
                                        target: 'new'
                                    });
                                });
                            })(day_attn);
                        } else if (attendance[j].status === 'holiday') {
                            td.style = "text-align:center; font-weight:600; color:Blue; font-size:15px; border-bottom:1px #525252 solid;";
                            td.textContent = "H";
                            var day_attn = attendance[j];
                            (function (day_attn) {
                                td.addEventListener("click", function () {
                                    self.action.doAction({
                                        name: _t("Holidays"),
                                        type: 'ir.actions.act_window',
                                        res_model: 'resource.calendar.leaves',
                                        domain: [["id", "in", [day_attn.ids]]],
                                        view_mode: 'list,form',
                                        views: [
                                            [false, 'list'],
                                            [false, 'form']
                                        ],
                                        target: 'new'
                                    });
                                });
                            })(day_attn);
                        } else {
                            // Verificar delay_status para aplicar colores
                            var delay_status = attendance[j].delay_status || 'on_time';
                            var bg_color = 'green';
                            var text_color = 'white';
                            
                            if (delay_status === 'minor') {
                                bg_color = '#ffeb3b';
                                text_color = 'black';
                            } else if (delay_status === 'unjustified_abs') {
                                bg_color = '#ff9800';
                                text_color = 'white';
                            }
                            
                            td.style = `text-align:center; font-weight:600; color:${text_color}; background-color:${bg_color}; font-size:13px; border-bottom:1px #525252 solid;`;
                            td.textContent = attendance[j].hours + ' H';
                            var day_attn = attendance[j];
                            (function (day_attn) {
                                td.addEventListener("click", function () {
                                    self.action.doAction({
                                        name: _t("Attendance"),
                                        type: 'ir.actions.act_window',
                                        res_model: 'hr.attendance',
                                        domain: [["id", "in", day_attn.ids]],
                                        view_mode: 'list,form',
                                        views: [
                                            [false, 'list'],
                                            [false, 'form']
                                        ],
                                        target: 'new'
                                    });
                                });
                            })(day_attn);
                        }
                    } else {
                        td.textContent = "A";
                    }
                    tr.appendChild(td);
                }
            }
            tbody.appendChild(tr);
        }
        
        // Añadir fila de totales
        var total_tr = document.createElement('tr');
        total_tr.style = "height:50px; background-color: white; font-weight: bold;";
        for (var j = 0; j <= days + 6; j++) {
            var td = document.createElement('td');
            if (j === 0) {
                td.style = "width:100px; min-width:100px; max-width:100px; border:1px solid white; padding:5px; text-align:center; background-color: white; font-weight: bold;";
                td.textContent = _t("TOTAL");
            } else if (j === days + 1) {
                td.style = "text-align:center; background-color:#e2ebb9; font-weight:700; font-size:15px; border:1px solid white;";
                td.textContent = total_p;
            } else if (j == days + 2) {
                td.style = "text-align:center; background-color:#ffc9c4; font-weight:700; font-size:15px; border:1px solid white;";
                td.textContent = total_a;
            } else if (j == days + 3) {
                td.style = "text-align:center; background-color:#ffe4b8; font-weight:700; font-size:15px; border:1px solid white;";
                td.textContent = total_l;
            } else if (j == days + 4) {
                td.style = "text-align:center; background-color:#bfd2ff; font-weight:700; font-size:15px; border:1px solid white;";
                td.textContent = total_h;
            } else if (j == days + 5) {
                td.style = "text-align:center; background-color:#ffeb3b; font-weight:700; font-size:15px; border:1px solid white;";
                td.textContent = total_md;
            } else if (j == days + 6) {
                td.style = "text-align:center; background-color:#ff9800; font-weight:700; font-size:15px; border:1px solid white;";
                td.textContent = total_ua;
            } else {
                td.style = "text-align:center; border:1px solid white; background-color: white;";
                td.textContent = "";
            }
            total_tr.appendChild(td);
        }
        tbody.appendChild(total_tr);
    }

    
    async getGreetings() {
        var self = this;
        const now = new Date();
        const hours = now.getHours();
        if (hours >= 5 && hours < 12) {
            self.greetings = _t("Good Morning");
        }
        else if (hours >= 12 && hours < 18) {
            self.greetings = _t("Good Afternoon");
        }
        else {
            self.greetings = _t("Good Evening");
        }
    }

    downloadReport(e) {
        e.stopPropagation();
        e.preventDefault();

        var opt = {
            margin: 1,
            filename: 'AttendanceDashboard.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'px', format: [1920, 1080], orientation: 'landscape' }
        };
        html2pdf().set(opt).from(document.getElementById("dashboard")).save()

    }

    createCheckIn(e) {
        e.stopPropagation();
        e.preventDefault();
        var self = this;

        self.action.doAction({
            name: _t("Check In"),
            type: 'ir.actions.act_window',
            res_model: 'check_in.check_in',
            domain: [],
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new'
        });
    }

    createBooking(e) {
        e.stopPropagation();
        e.preventDefault();
        var self = this;

        self.action.doAction({
            name: _t("Booking"),
            type: 'ir.actions.act_window',
            res_model: 'dev.book.hotel',
            domain: [],
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new'
        });
    }

    // _downloadExcelReport() {
    //     const filter = this.state.requestData;
    
    //     // Convert to query string
    //     const query = new URLSearchParams(filter).toString();
    
    //     // Trigger file download
    //     window.open('/attendance/report/download?' + query, '_blank');
    // }
    

    renderAttendanceDashboardFilter() {
        rpc('/render_attendance_dashboard_filter').then(function (data) {
            var employees = data[0]
            var departments = data[1]

            var employeeSelection = document.getElementById('employee_selection');

            employees.forEach(function (employee) {
                var option = document.createElement('option');
                option.value = employee.id;
                option.textContent = employee.name;
                employeeSelection.appendChild(option);
            });

            var departmentSelection = document.getElementById('department_selection');

            departments.forEach(function (department) {
                var option = document.createElement('option');
                option.value = department.id;
                option.textContent = department.name;
                departmentSelection.appendChild(option);
            });

            

            const date = new Date();
            const monthNames = [_t("January"), _t("February"), _t("March"), _t("April"), _t("May"), _t("June"), _t("July"), _t("August"), _t("September"), _t("October"), _t("November"), _t("December")];

            var monthSelection = document.getElementById("month_selection")
            for (var i = 0; i < monthNames.length; i++) {
                var option = document.createElement('option');
                if (i == date.getMonth()) {
                    option.value = i;
                    option.textContent = monthNames[i];
                    option.selected = true;
                } else {
                    option.value = i;
                    option.textContent = monthNames[i];
                }
                monthSelection.appendChild(option);
            }

            var yearSelection = document.getElementById("year_selection")
            // Incluir año siguiente, año actual y 5 años anteriores
            for (var i = -1; i <= 5; i++) {
                var year = date.getFullYear() - i
                var option = document.createElement('option');
                if (year == date.getFullYear()) {
                    option.value = year;
                    option.textContent = year;
                    option.selected = true;
                } else {
                    option.value = year;
                    option.textContent = year;
                }
                yearSelection.appendChild(option);
            }

            
        })
    }

    
    _onchangeAttendanceFilter(ev) {
        const employeeSelect = document.querySelector('#employee_selection');
        const departmentSelect = document.querySelector('#department_selection');
        const monthSelect = document.querySelector('#month_selection');
        const yearSelect = document.querySelector('#year_selection');
    
        let employee_selection = employeeSelect?.value || 'all';
        const department_selection = departmentSelect?.value || 'all';
        const month_selection = monthSelect?.value || 'all';
        const year_selection = yearSelect?.value || 'all';
    
        // If department is changed, refresh the employee list
        if (ev.target.id === 'department_selection') {
            rpc('/get_employees_by_department', {
                department_id: department_selection
            }).then((result) => {
                employeeSelect.innerHTML = '';
        
                const allOption = document.createElement('option');
                allOption.value = 'all';
                allOption.textContent = _t('All Employees');
                employeeSelect.appendChild(allOption);
        
                result.forEach(emp => {
                    const option = document.createElement('option');
                    option.value = emp.id;
                    option.textContent = emp.name;
                    employeeSelect.appendChild(option);
                });
        
                employee_selection = 'all';
            });
        }
    
        // Prepare the data for attendance fetch
        const requestData = {
            employee: employee_selection,
            department: department_selection,
            month: month_selection,
            year: year_selection,
        };
    
        // Fetch dashboard and leave details
        this.getAttendanceData(requestData);
        this.getAttendanceCounterData(requestData);
        this.state.requestData = requestData;
        this.getLeaveDetail(this.state.requestData, this.state.rowsPerPage, this.state.currentPage);

        console.log("Updated filters:", this.state.requestData);
    }

    getAttendanceCounterData(requestData) {
        // rpc.query({
        //     route: '/get/attendance/tiles/data',
        //     params: requestData,
        // }).then((result) => {
        //     // Update your UI based on the result
        //     console.log("Tile Data:", result);
        var self = this;
        rpc('/get/attendance/tiles/data', { 'request': requestData }).then(function (result) {
            
            
            self.state.all_employee_data = result['all_employee_data']
            self.state.all_present = result['all_present']
            self.state.all_absent = result['all_absent']
            self.state.on_leave = result['on_leave']
            self.state.late_checkin = result['late_checkin']
            // Contadores para el día actual
            self.state.all_present_today = result['all_present_today'] || []
            self.state.all_absent_today = result['all_absent_today'] || []
            self.state.on_leave_today = result['on_leave_today'] || []
            self.state.late_checkin_today = result['late_checkin_today'] || []
            
            
            // document.querySelector('#all_present').innerHTML = result.all_present.length;
            // document.querySelector('#all_present').innerHTML = result.all_absent.length;
            // document.querySelector('#all_present').innerHTML = result.on_leave.length;
            // document.querySelector('#all_present').innerHTML = result.late_checkin.length;
        })
    
            
    }

    
    
    getLeaveDetail(requestData, rowsPerPage, currentPage) {
        var self = this;
        console.log("called", requestData, rowsPerPage, currentPage);
        
        rpc('/employee/leave', { 'request': requestData }).then(function (response) {
            var tbody = document.querySelector("#leaveDetail tbody");
            tbody.innerHTML = ' ';
            console.log(response);
            console.log(self.state.leave_summary);
            
            self.state.leave_summary = response
            console.log(self.state.leave_summary);

            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            console.log(start, end);
            
            const paginatedData =  self.state.leave_summary.slice(start, end)
            console.log("paginatedData",paginatedData);

            
            for (var i = 0; i < paginatedData.length; i++) { // CHANGE HERE: 'i <' instead of 'i <='
                var tr = document.createElement('tr');
                const newBtn = document.createElement('button');
                newBtn.textContent = _t('View');
                newBtn.style = "background-color: #71639e; color: white;";
                newBtn.className = "btn btn-primary";
                
                for (var key in paginatedData[i]) {
                    if (key === 'id') {
                        newBtn.value = paginatedData[i][key];
                        continue; 
                    }
                
                    if (key === 'request_date_from') {
                        var cell = document.createElement("td");
                        var date = paginatedData[i]['request_date_from'];
                        if (date) {
                            var arr1 = date.split('-');
                            cell.textContent = arr1[2] + '-' + arr1[1] + '-' + arr1[0];
                        } else {
                            cell.textContent = '-';
                        }
                        tr.appendChild(cell);
                        
                    }
                    else if (key === 'request_date_to') { 
                        var cell = document.createElement("td"); 
                        var dates = paginatedData[i]['request_date_to'];
                        if (dates) {
                            var arr1 = dates.split('-');
                            cell.textContent = arr1[2] + '-' + arr1[1] + '-' + arr1[0];
                        } else {
                            cell.textContent = '-';
                        }
                        tr.appendChild(cell);
                    }
                    else { // This 'else' block will now correctly handle 'state', 'name', and other general data fields
                        let td = document.createElement('td');
                        if (Array.isArray(paginatedData[i][key]) && paginatedData[i][key].length === 2) {
                            td.textContent = paginatedData[i][key][1];
                        } else if (paginatedData[i][key] === false) {
                            td.textContent = '-';
                        } else {
                            td.textContent = paginatedData[i][key];
                        }
                        tr.appendChild(td);
                    }
            
                                       
                }
            
                // ADD THIS BLOCK HERE:
                // This ensures the button cell is always the last <td> in the row.
                var btnCell = document.createElement('td');
                btnCell.appendChild(newBtn);
                tr.appendChild(btnCell);
            
            
                tbody.appendChild(tr);
                newBtn.addEventListener('click', function () {
                    viewLeave(newBtn.value);
                });
            }
        })

        function viewLeave(id) {
            var options = {
            };
            self.action.doAction({
                name: _t("Leave"),
                type: 'ir.actions.act_window',
                res_model: 'hr.leave',
                res_id: parseInt(id),
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new'
            }, options)
        }
    }

    prevPage(e) {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            this.getLeaveDetail(this.state.requestData, this.state.rowsPerPage, this.state.currentPage);
            document.getElementById("next_button").disabled = false;
        }
        if (this.state.currentPage == 1) {
            document.getElementById("prev_button").disabled = true;
        } else {
            document.getElementById("prev_button").disabled = false;
        }
    }

    nextPage() {
        if ((this.state.currentPage * this.state.rowsPerPage) < this.state.leave_summary.length) {
            this.state.currentPage++;
            this.getLeaveDetail(this.state.requestData, this.state.rowsPerPage, this.state.currentPage);
            document.getElementById("prev_button").disabled = false;
        }
        if (Math.ceil(this.state.leave_summary / this.state.rowsPerPage) == this.state.currentPage) {
            document.getElementById("next_button").disabled = true;
        } else {
            document.getElementById("next_button").disabled = false;
        }
    }


    
}
AttendanceDashboard.template = "AttendanceDashboard"
registry.category("actions").add("attendance_dashboard", AttendanceDashboard)
