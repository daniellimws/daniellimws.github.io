package main

import (
	"compress/gzip"
	"crypto/aes"
	"crypto/cipher"
	"encoding/hex"
  "fmt"
	"crypto/rand"
	"io"
	"bytes"
	"encoding/json"
	"io/ioutil"
	"github.com/sensepost/godoh/protocol"

	"strconv"
	"strings"
)

const cryptKey = `8a40cdd5c4608b251b2c5926270540dc`

// GunzipWrite data to a Writer
func GunzipWrite(w io.Writer, data []byte) error {
	// Write gzipped data to the client
	gr, err := gzip.NewReader(bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	defer gr.Close()

	data, err = ioutil.ReadAll(gr)
	if err != nil {
		return err
	}
	w.Write(data)

	return nil
}

func UngobUnpress(s interface{}, data []byte) error {

	dcData := bytes.Buffer{}
	if err := GunzipWrite(&dcData, data); err != nil {
		return err
	}

	// Decrypt the data
	decryptData := Decrypt(dcData.Bytes())

	if err := json.Unmarshal(decryptData, &s); err != nil {
		return err
	}

	return nil
}

// Encrypt will encrypt a byte stream
// https://golang.org/pkg/crypto/cipher/#NewCFBEncrypter
func Encrypt(plaintext []byte) ([]byte, error) {
	key, _ := hex.DecodeString(cryptKey)

	block, err := aes.NewCipher(key)
	if err != nil {
		panic(err)
	}

	// The IV needs to be unique, but not secure. Therefore it's common to
	// include it at the beginning of the ciphertext.
	ciphertext := make([]byte, aes.BlockSize+len(plaintext))
	iv := ciphertext[:aes.BlockSize]
	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return nil, err
	}

	stream := cipher.NewCFBEncrypter(block, iv)
	stream.XORKeyStream(ciphertext[aes.BlockSize:], plaintext)

	return ciphertext, nil
}

// Decrypt will decrypt a byte stream
// https://golang.org/pkg/crypto/cipher/#example_NewCFBDecrypter
func Decrypt(ciphertext []byte) ([]byte) {
	key, _ := hex.DecodeString(cryptKey)

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil
	}

	// The IV needs to be unique, but not secure. Therefore it's common to
	// include it at the beginning of the ciphertext.
	if len(ciphertext) < aes.BlockSize {
		return nil
	}

	iv := ciphertext[:aes.BlockSize]
	ciphertext = ciphertext[aes.BlockSize:]

	stream := cipher.NewCFBDecrypter(block, iv)

	// XORKeyStream can work in-place if the two arguments are the same.
	stream.XORKeyStream(ciphertext, ciphertext)

	return ciphertext
}

// parseARRLabels splits and parses relevant labels from a question
func parseARRLabels(query string) ([]byte) {

	// A hostnames labels are what is interesting to us. Extract them.
	hsq := strings.Split(query, ".")

	// dataLen is used only in this function to determine the concat
	// amount for data itself.
	dataLen, _ := strconv.Atoi(hsq[5])

	// build up the data variable. We assume of a label was 0
	// then the data is not interesting.
	var data string
	switch dataLen {
	case 1:
		data = hsq[6]
		break
	case 2:
		data = hsq[6] + hsq[7]
		break
	case 3:
		data = hsq[6] + hsq[7] + hsq[8]
		break
	}

	// decode the data
	byteData, _ := hex.DecodeString(data)

	return byteData
}

func main() {
  // c, _ := Encrypt([]byte("Daniel Lim"))

  dataBytes, _ := hex.DecodeString("1f8b08000000000002ff00af0050ff044f1a467dab6b9371a8cbd55cce223a2573f4144345f8a1d43d7db33258a794d5da83bfabbe5ac3ab36f9c2b9b034091202a6dc5dd67f0d42cc641c379f89de12a56214b519d468347eea14a7ef621e4f3ff9c9b86185b663b4490379da470226b4ad98b3500ef75d241afae01cdd0e1e0f22760b44f8bb2fb1f9ff308b2565d5d2fb59988723ce11e8bc68186ff4b768244f79dc5503ceafb9b60841f9ce7869c048644a318e9196358851879d4d010000ffff3cd91697af000000")
  // d := Decrypt(dataBytes)

  // var command string
  // UngobUnpress(&command, dataBytes)

  cp := &protocol.Command{}
  UngobUnpress(cp, dataBytes)

  fmt.Println(string(cp.Data))

  // s := parseARRLabels("3<1f8b08000000000002ff00af0050ff044f1a467dab6b9371a8cbd55cce22<3a2573f4144345f8a1d43d7db33258a794d5da83bfabbe5ac3ab36f9c2b9<b034091202a6dc5dd67f0d42cc641c379f89de12a56214b519d468347eea.")
  // fmt.Println(string(s))
}