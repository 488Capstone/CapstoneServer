from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from .aws_controller import get_items, update_zip, get_device_shadow

# make a blueprint of views for app
views = Blueprint('views', __name__)


@views.route('/water_start_stop', methods=['POST'])
@login_required
def water_start_stop():
    try:
        return jsonify(success=1)
    except Exception as e:
        return jsonify(success=0, error_msg=str(e))


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():

    items = get_items(current_user.device_id)
    headings = ("Sample Time", "Temperature", "Moisture", "Status", "Battery Level")
    items.reverse()
    data = items[1:11]

    shadow = get_device_shadow(current_user.device_id)
    print(f'shadow to views: {shadow}')
    reported_zipcode = shadow["state"]["reported"].get("zip")
    desired_zipcode = shadow["state"]["desired"].get("zip")

    if reported_zipcode == desired_zipcode:
        display_zip = reported_zipcode
    else:
        display_zip = desired_zipcode

    print(f'display zip is {display_zip}')

    properties = {'device_id': str(current_user.device_id), 'zip': display_zip}

    return render_template('home.html', headings=headings, data=data, properties=properties, user=current_user)


@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new_zip = request.form.get('zip')
        update_zip(1, new_zip)

        flash('ZIP update sent')
        return redirect(url_for('views.home'))
    return render_template("settings.html", user=current_user)
