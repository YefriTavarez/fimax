## FiMax (UNDER DEVELOPMENT)

FiMax is an application built on top of [Frappe Framework](https://github.com/frappe/frappe) intended to manage loans a repayment schedules for Customers.

Most of the work is done by Frappe and also it integrates with [ERPNext](https://github.com/frappe/erpnext), another application built on Frappe.

### Installation

The preferred way to install this app is using the [bench](https://github.com/frappe/bench) app provided by Frappe Contributors.

We recomend installing ERPNext before installing this app as it reuses most of the funcionalities written in the former.

* Download the app and get it ready to install in the Framework
		
		bench get-app fimax https://github.com/YefriTavarez/fimax.git
		
* Install the application to the site

		bench --site sitename install-app fimax
		
* Reload the bench for the changes to take efect (this is done automatically if sudoers are setup)

		bench restart 

### License

GNU/General Public License

The Fimax code is licensed as GNU General Public License (v3) and the Documentation is licensed as Creative Commons (CC-BY-SA-3.0) and the copyright is owned by TZCODE, SRL and Contributors.

