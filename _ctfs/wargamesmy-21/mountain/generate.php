<?php
function genpassverify($length = 10) {
$verify_code = mt_rand(1000000000,9999999999);
mt_srand($verify_code);
$acc_passwd = mt_rand();
return $acc_passwd.':'.$verify_code;
}
?>
