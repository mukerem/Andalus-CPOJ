var nav_dropdown = document.querySelector('.ur-nav-dropdown');
var nav_dpd_btn = nav_dropdown.querySelector('.ur-nav-dropdown-title');
var nav_dpd_body = nav_dropdown.querySelector('.ur-nav-dropdown-body');
var body_height = nav_dpd_body.offsetHeight;

nav_dpd_body.style.height = '0';
nav_dpd_body.style.visibility = 'hidden';

let status_dpd = true;
nav_dpd_btn.addEventListener('click', function() {
    if(status_dpd) {
        nav_dpd_body.style.height = body_height.toString() + 'px';
        nav_dpd_body.style.visibility = 'visible';
        status_dpd = false;
    } else {
        nav_dpd_body.style.height = '0';
        nav_dpd_body.style.visibility = 'hidden';
        status_dpd = true;
    }

    window.addEventListener('click', function(event) {
        var trgt = event.target;

        if(trgt != nav_dpd_body && trgt != nav_dropdown && trgt != nav_dpd_btn && trgt.className != 'ur-nav-link') {
            nav_dpd_body.style.height = '0';
            nav_dpd_body.style.visibility = 'hidden';
            status_dpd = true;
        }
    });

});

/*--- nav btn ---*/
if(window.innerWidth <= 768) {
    var nav_btn = document.querySelector('.ur-nav-btn');
    var nav_body = document.querySelector('.ur-nav ul');

    var height = nav_body.offsetHeight;

    nav_body.style.height = '0';
    nav_body.style.visibility = 'hidden';

    let status = true;

    nav_btn.addEventListener('click', function() {
        if(status) {
            nav_body.style.height = height.toString() + 'px';
            nav_body.style.visibility = 'visible';
            status = false;
        } else {
            nav_body.style.height = '0';
            nav_body.style.visibility = 'hidden';
            status = true;
        }
    });
}
