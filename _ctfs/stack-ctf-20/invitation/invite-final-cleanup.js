x = [0, 0, 0];

const compare = (a, b) => { let s = ''; for (let i = 0; i < Math.max(a.length, b.length); i++) { s += String.fromCharCode((a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0)) } return s };
if (location.protocol == 'file:') { x[0] = 23 } else { x[0] = 57 }

if (compare(window.location.hostname, "you're invited!!!") == unescape("%1E%00%03S%17%06HD%0D%02%0FZ%09%0BB@M")) {
    x[1] = 88
} else {
    x[1] = 31
}

function yyy() {
    var uuu = false;
    var zzz = new Image();
    Object.defineProperty(zzz, 'id', {
        get: function() {
            uuu = true;
            x[2] = 54
        }
    });
    requestAnimationFrame(function X() {
        uuu = false;
        console.log("%c", zzz);
        if (!uuu) { x[2] = 98 }
    })
};
yyy();

function ooo(seed) { var m = 0xff; var a = 11; var c = 17; var z = seed || 3; return function() { z = (a * z + c) % m; return z } }

function iii(eee) {
    ttt = eee[0] << 16 | eee[1] << 8 | eee[2];
    rrr = ooo(ttt);
    ggg = window.location.pathname.slice(1);
    hhh = "";
    for (i = 0; i < ggg.length; i++) {
        hhh += String.fromCharCode(ggg.charCodeAt(i) - 1)
    }
    vvv = atob("3V3jYanBpfDq5QAb7OMCcT//k/leaHVWaWLfhj4=");
    hhh = "govtech-ctf"
    mmm = "";
    if (hhh.slice(0, 2) == "go" && hhh.charCodeAt(2) == 118 && hhh.indexOf('ech-c') == 4) {
        for (i = 0; i < vvv.length; i++) { mmm += String.fromCharCode(vvv.charCodeAt(i) ^ rrr()) }
        console.log(mmm);
        // alert("Thank you for accepting the invite!"+hhh+mmm)
    }
}

function jjj(n) {
    rrr = ooo(n);
    ggg = window.location.pathname.slice(1);
    hhh = "";
    for (i = 0; i < ggg.length; i++) {
        hhh += String.fromCharCode(ggg.charCodeAt(i) - 1)
    }
    vvv = atob("3V3jYanBpfDq5QAb7OMCcT//k/leaHVWaWLfhj4=");
    hhh = "govtech-ctf"
    mmm = "";
    if (hhh.slice(0, 2) == "go" && hhh.charCodeAt(2) == 118 && hhh.indexOf('ech-c') == 4) {
        for (i = 0; i < vvv.length; i++) { mmm += String.fromCharCode(vvv.charCodeAt(i) ^ rrr()) }
        console.log(mmm);
        // alert("Thank you for accepting the invite!"+hhh+mmm)
    }
}

for (a = 0; a != 1000; a++) {}
$('.custom1').catLED({ type: 'custom', color: '#FF0000', background_color: '#e0e0e0', size: 10, rounded: 5, font_type: 4, value: " YOU'RE INVITED! " });
$('.custom2').catLED({ type: 'custom', color: '#FF0000', background_color: '#e0e0e0', size: 10, rounded: 5, font_type: 4, value: "                 " });
$('.custom3').catLED({ type: 'custom', color: '#FF0000', background_color: '#e0e0e0', size: 10, rounded: 5, font_type: 4, value: "   WE WANT YOU!  " });

// 23, 57
// 88, 31
// 54, 98

iii([57, 88, 54])

// {gr33tz_w3LC0m3_2_dA_t3@m_m8}