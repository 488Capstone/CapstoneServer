$('#btnradio1').change(function() {
    // alert(this.checked);

    $.post('/water_start_stop', {"water_start_stop": "start"}, function (results) {

        if (results.success) {
            alert(this.checked);
            toggleAlert()





        } else {
            $('#dangerAlert').message('Update Failed; '+ results.error_msg)
        }


        }



    );

});

function toggleAlert(){
    $(".alert").toggleClass('in out');
    return false
}
$('#bsalert').on('close.bs.alert', toggleAlert)

// sample with return function:
// data = $('#my-form').serialize()
// $.post(update_url, data, function (results) {
//     // Here you check results.
//     if (results.success) {
//         $('#update-div').message('Update Success')
//     } else {
//         $('#update-div').message('Update Failed: ' + results.error_msg)
//     }
// })