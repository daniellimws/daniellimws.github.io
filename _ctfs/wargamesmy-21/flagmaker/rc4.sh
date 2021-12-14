#!/bin/bash
################################################################################
# file:		rc4.sh
# created:	15-05-2011
# modified:	2014 Sep 04
#
# https://secure.wikimedia.org/wikipedia/en/wiki/RC4
#
# NOTES:
#   - ord() & chr() from http://mywiki.wooledge.org/BashFAQ/071
#
# TODO:
#   - todo figure out a better way for all the conversions
#   - optimize =)
#   - improve the s-box drawing thingie to only print changed bytes
#
################################################################################
set -u
shopt -s nocasematch
declare     TITLE="rc4.sh -- the RC4 stream cipher"
declare -a  S=()
declare -ai KEY=()
declare -i  KEYLENGTH
# Two 8-bit index-pointers
declare -i  I
declare -i  J
# keystream
declare -i  K
declare -i  SWAPBYTE
declare -i  DEBUG=0
# mode
declare -i  ENCRYPT=1
declare -i  NCHARS=1
declare     CIPHERTEXT=
declare HL1="\033[44;1;31m"
declare HL2="\033[1m"
STDIN_TYPE=$(stat -L -c %F /proc/self/fd/0)

function ord() {
  # ord() - converts ASCII character to its decimal value
  [ ${#1} -ne 1 -o ${#} -ne 1 ] && echo "${FUNCNAME}(): error!" 1>&2
  printf '%d' "'${1}"
  return ${?}
}

function chr() {
  # chr() - converts decimal value to its ASCII character representation
  case ${1} in
    # this is stupid, but i couldn't figure out any other way to do this. we
    # use "echo -en" to print the decrypted ciphertext.
    10)
      echo -n '\n'
    ;;
    *)
      printf \\$(printf '%03o' ${1})
    ;;
  esac
  return ${?}
}

function usage() {
  cat 0<<-EOF
	${TITLE}

	usage: ${0##*/} options

	this script encrypts and decrypts data with the RC4 stream cipher algorithm. the script reads data from stdin and outputs the encrypted or decrypted data to stdout. if you're decrypting, the encrypted data must be hex encoded (e.g. "1021BF0420").

	so to encrypt data, you can do:
	echo -n "pedia" | ./rc4.sh -k Wiki

	and to decrypt, do:
	echo -n "1021BF0420" | ./rc4.sh -d -k Wiki

	you can try the test vector's from wikipedia (https://en.wikipedia.org/wiki/RC4#Test_vectors):

	echo -n "Plaintext" | bash ./rc4.sh -k Key
	echo -n "pedia" | bash ./rc4.sh -k Wiki
	echo -n "Attack at dawn" | bash ./rc4.sh -k Secret

	options:
	  -d		decrypt (the default is to encrypt)
	  -h		this help
	  -k key	key
	  		you can provide the key as hex by prefixing with '0x',
	  		it is otherwise interpreted as ASCII.

	  -x		debug mode
EOF
  #	  -c ciphertext	ciphertext as hexadecimal (e.g. "1021BF0420")
  #	  #-p plaintext	plaintext
} # usage()

function draw_s-box() {
  # $1 = I
  # $2 = J
  local -i I=0
  local    K_HEX
  local    NO_COLOUR
  local    HL

  if [ ${#} -ne 2 -o -z "${1}" -o -z "${2}" ]
  then
    echo "${FUNCNAME}(): error!" 1>&2
    return 1
  fi

  #for ((I=0; I<=46; I++))
  #do
  #  echo -n "-"
  #done
  #echo -n $'\n'
  for ((I=0; I<256; I++))
  do
    printf -v K_HEX '%.2x' ${S[I]}

    HL=""
    NO_COLOUR=""

    # colours
    # http://tldp.org/LDP/abs/html/colorizing.html
    if [ ${I} -eq ${1} -o ${I} -eq ${2} ]
    then
      # I or J
      HL="\033[1m"
      NO_COLOUR="\033[0m"
    elif [ ${I} -eq $(( ( S[${1}] + S[${2}] ) % 256 )) ]
    then
      # keystream byte
      HL="${HL1}"
      NO_COLOUR="\033[0m"
    fi

    # print the value
    echo -en "${HL}${K_HEX}${NO_COLOUR} " 1>&2

    if [ $(( I % 16 )) -eq 15 ]
    then
      # newline
      echo -n $'\n'
    fi 1>&2

  done
  echo -n $'\n' 1>&2
  return 0
} # draw_s-box()
ASCIIKEY="w4rgames.my"
KEYLENGTH=${#ASCIIKEY}
while getopts "dhk:c:p:x" OPTION
do
  case "${OPTION}" in
    "d")
      ENCRYPT=0
      NCHARS=2
    ;;
#    "k")
#      ASCIIKEY="${OPTARG}"
#      if [ "${ASCIIKEY:0:2}" = "0x" ]	# key provided as hex
#      then
#	KEYLENGTH=$[ ( ${#ASCIIKEY} - 2 ) / 2 ]
#	#echo "DEBUG: keylength=${KEYLENGTH}"
#      else				# key provided as ASCII
#        KEYLENGTH=${#ASCIIKEY}
#      fi
#    ;;
    #"c")
    #  # ciphertext provided -> decrypt mode
    #  CIPHERTEXT="${OPTARG}"
    #  LENGTH=$[${#CIPHERTEXT}/2]
    #  ENCRYPT=0
    #  NCHARS=2
    #;;
    #"p")
    #  # plaintext provided -> encrypt mode
    #  PLAINTEXT="${OPTARG}"
    #  LENGTH=${#PLAINTEXT}
    #  ENCRYPT=1
    #  NCHARS=1
    #;;
    "x") DEBUG=1 ;;
    "h"|*)
      usage
      exit 0
    ;;
  esac
done

#if [ ${#} -eq 0 ]
#then

  #exit 0
#fi
# sanity checks
[ -z "${ASCIIKEY}" ] && {
  echo "error: no key provided!" 1>&2
  exit 1
}
[ ${KEYLENGTH} -lt 1 -o ${KEYLENGTH} -gt 256 ] && {
  echo "error: invalid keylength!" 1>&2
  exit 1
}
#if (( ${ENCRYPT} )) && [ -n "${CIPHERTEXT}" ]
#then
#  echo "error: mode is encrypt and you provided the ciphertext?" 1>&2
#  exit 1
#elif (( ${ENCRYPT} )) && [ -z "${PLAINTEXT}" ]
#then
#  echo "error: mode is encrypt and no plaintext provided!" 1>&2
#  exit 1
#elif (( ! ${ENCRYPT} )) && [ -n "${PLAINTEXT}" ]
#then
#  echo "error: mode is decrypt and you provided the plaintext?" 1>&2
#  exit 1
#elif (( ! ${ENCRYPT} )) && [ -z "${CIPHERTEXT}" ]
#then
#  echo "error: mode is decrypt and no ciphertext provided!" 1>&2
#  exit 1
#elif (( ! ${ENCRYPT} )) && [ $[ ${#CIPHERTEXT} % 2 ] -ne 0 ]
#then
#  echo "error: invalid ciphertext!" 1>&2
#  exit 1
#fi

for ((I=0; I<${KEYLENGTH}; I++))
do
  if [ "${ASCIIKEY:0:2}" = "0x" ]	# key provided as hex
  then
    # hex to dec
    let KEY[I]=0x${ASCIIKEY:$[(I+1)*2]:2}
    #echo "DEBUG: KEY[${I}]=${KEY[I]}"
  else					# key provided as ASCII
    # translate the ASCII key to decimal
    KEY[I]=`ord "${ASCIIKEY:${I}:1}"`
    #echo "DEBUG: KEY[${I}]=${ASCIIKEY:${I}:1}"
  fi
done

cat 0<<-EOF 1>&2

	starting up the flag maker engine...
EOF

S=( {0..255} )

# The key-scheduling algorithm (KSA)
J=0
for I in {0..255}
do
  J=$[ ( J + S[I] + KEY[ I % KEYLENGTH ] ) % 256 ]
  SWAPBYTE=${S[I]}
  # S-Box (Substitution-box)
  S[I]=${S[J]}
  S[J]=${SWAPBYTE}
  if (( ${DEBUG} )) && [ ${I} -eq 0 ]
  then
    echo "  DEBUG: I=${I} J=${J} S[${I}]=${S[I]} S[${J}]=${S[J]}" 1>&2
  fi
done

echo -e "Initiating flag launching sequence...\n" 1>&2

if (( ${DEBUG} ))
then
  clear
fi 1>&2

# The pseudo-random generation algorithm (PRGA)
I=0
J=0
COUNTER=0
#for ((I=0, J=0, COUNTER=0; COUNTER<${LENGTH}; COUNTER++))
while read -rs -d "" -n ${NCHARS}
do
  # end-of-transmission
  # ./rc4.sh: line 256: [: `)' expected, found
  #if [ "${STDIN_TYPE}" = "character special file" -a "${REPLY}" = $'\x04' ]
  if \
    [ "${STDIN_TYPE}" = "character special file" ] && \
      [[ "${REPLY}" == $'\x04' ]]
  then
    echo "EOT received" 1>&2
    break
  fi
  I=$[ ++I		% 256 ]
  J=$[ ( J + S[I] )	% 256 ]
  SWAPBYTE=${S[I]}
  S[I]=${S[J]}
  S[J]=${SWAPBYTE}
  # keystream
  K=$[ S[ ( S[I] + S[J] ) % 256 ] ]
  # decimal to hexadecimal
  printf -v K_HEX '%.2x' ${K}

  # these are the same for both encrypt and decrypt.
  if (( ${DEBUG} ))
  then
    echo -en "\033[1;1H"
#    cat 0<<-EOF 1>&2
#	DEBUG (character $[COUNTER+1]/${LENGTH}):
#	  I=${I} J=${J} S[I]=${S[I]} S[J]=${S[J]}
#EOF
    printf "DEBUG (character #$((++COUNTER))):\n"
    printf "  I=%3d J=%3d S[I]=${HL2}%.2x\033[0m S[J]=${HL2}%.2x\033[0m\n" ${I} ${J} ${S[I]} ${S[J]}
    echo -e "  keystream byte (hex)\t= ${HL1}${K_HEX}\033[0m"
  fi 1>&2
  # encrypt or decrypt?
  if (( ${ENCRYPT} ))
  then # encrypt
    #CHAR="${PLAINTEXT:${COUNTER}:1}"
    CHAR="${REPLY}"
    CHARCODE=`ord "${CHAR}"`
    # "As with any stream cipher, these can be used for encryption by combining it with the plaintext using bit-wise exclusive-or"
    ENCRYPTED_CHARCODE=$[ CHARCODE ^ K ]
    #ENCRYPTED_CHAR=`chr ${ENCRYPTED_CHARCODE}`
    printf -v ENCRYPTED_CHARCODE_HEX '%.2x' ${ENCRYPTED_CHARCODE}
    if (( ${DEBUG} ))
    then
#      cat 0<<-EOF 1>&2
#	  ENCRYPTED_CHARCODE (dec)	= ${ENCRYPTED_CHARCODE}
#	  ENCRYPTED_CHARCODE (hex)	= ${ENCRYPTED_CHARCODE_HEX}
#	  CHAR (dec)			= ${CHARCODE}
#	  CHAR				= "${CHAR}"
#
#EOF
      printf "  ciphertext (dec)\t= %3d\n" ${ENCRYPTED_CHARCODE}
      printf "  ciphertext (hex)\t= %s\n" ${ENCRYPTED_CHARCODE_HEX}
      printf "  plaintext (dec)\t= %3d\n" ${CHARCODE}
      printf "  plaintext (hex)\t= %.2x\n" ${CHARCODE}
      # https://en.wikipedia.org/wiki/ASCII#ASCII_printable_characters
      # TODO: for some reason space (0x20) displays as """
      if [ ${CHARCODE} -ge 32 -a ${CHARCODE} -le 126 ]
      then
	printf "  plaintext\t\t= \"%c\"\n\n" "${CHAR}"
      else
	printf "  plaintext\t\t= \" \"\n\n"
      fi
      draw_s-box "${I}" "${J}"
    fi 1>&2
    CIPHERTEXT="${CIPHERTEXT}${ENCRYPTED_CHARCODE_HEX}"
    PLAINTEXT+="${CHAR}"
  else # decrypt

    # NOTE: we don't need or want the ciphertext as a character, since it can
    #       be anything.
    #ENCRYPTED_CHARCODE_HEX=${CIPHERTEXT:$[COUNTER*2]:2}
    ENCRYPTED_CHARCODE_HEX=${REPLY}

    # check that the input was hex encoded
    if [[ ! ${ENCRYPTED_CHARCODE_HEX} =~ ^[0-9a-f]{2}$ ]]
    then
      echo "error: ciphertext not in hex! aborting." 1>&2
      exit 1
    fi

    # hexadecimal to decimal
    # http://unstableme.blogspot.com/2007/12/hex-to-decimal-conversion-bash-newbie.html
    # ./rc4.sh: line 331: let: ENCRYPTED_CHARCODE=0xa: syntax error: invalid arithmetic operator (error token is "")
    let ENCRYPTED_CHARCODE=0x${ENCRYPTED_CHARCODE_HEX}

    DECRYPTED_CHARCODE=$[ ENCRYPTED_CHARCODE ^ K ]
    DECRYPTED_CHAR=`chr ${DECRYPTED_CHARCODE}`
    if (( ${DEBUG} ))
    then
#      cat 0<<-EOF 1>&2
#	  ENCRYPTED_CHARCODE (dec)	= ${ENCRYPTED_CHARCODE}
#	  ENCRYPTED_CHARCODE (hex)	= ${ENCRYPTED_CHARCODE_HEX}
#	  DECRYPTED_CHAR		= "${DECRYPTED_CHAR}"
#EOF
      printf "  ciphertext (dec)\t= %3d\n"	${ENCRYPTED_CHARCODE}
      printf "  ciphertext (hex)\t= %s\n"	${ENCRYPTED_CHARCODE_HEX}
      printf "  plaintext (dec)\t= %d\n"	${DECRYPTED_CHARCODE}
      printf "  plaintext (hex)\t= %.2x\n"	${DECRYPTED_CHARCODE}
      if [ ${DECRYPTED_CHARCODE} -ge 32 -a ${DECRYPTED_CHARCODE} -le 126 ]
      then
        printf "  plaintext\t\t= \"%c\"\n\n" ${DECRYPTED_CHAR}
      else
        printf "  plaintext\t\t= \" \"\n\n"
      fi
    fi 1>&2
    PLAINTEXT+="${DECRYPTED_CHAR}"
  fi
done

if (( ${ENCRYPT} ))
then
  # some error checking
  if [ $[ ${#CIPHERTEXT} % 2 ] -ne 0 ]
  then
    echo "error: invalid ciphertext!" 1>&2
  fi
  # print the end result
  echo -en "\nciphertext (hex):\t" 1>&2
  echo -e "${CIPHERTEXT^^}"
  echo -en "\nplaintext:\t\t" 1>&2
  echo -e "${PLAINTEXT}"
  if [ ${CIPHERTEXT^^} == "DD38593CEC368BE7DFC709E59A4878F7C462D6BD6E128515B39CCE1E94012814C056821E976D" ]
  then
    printf "Flag has been launch!!!! Submit your flag\n\n"
  else
    printf "Flag launching sequence failed!\n\n"
  fi
else
  # decrypted
  echo -en "\nplaintext:\t" 1>&2
  echo -en "${PLAINTEXT}"
  #printf "%s" ${PLAINTEXT}
  echo -n $'\n' 1>&2
fi

exit
