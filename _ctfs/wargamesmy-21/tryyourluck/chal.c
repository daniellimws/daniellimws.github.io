#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>

int main(int argc, char const *argv[])
{
	// Generate number using random seed
	unsigned char seed[4];
	int fd = open("/dev/urandom", O_RDONLY);
	read(fd, seed, 4);
	close(fd);
	srand(*(unsigned int *)seed);

	float money = 1000.00f;
	float bet = 0;
	int number = 0;
	int guess = 0;

	printf("Try your luck with this simple guessing game!\n");
	printf("You only have 10 chances to bet and guess\n");
	printf("Get the flag if you win one billion\n");
	printf("Good Luck!!\n\n");
	fflush(stdout);

	for (int i = 0; i < 10; ++i)
	{
		printf("Enter bet: ");
		fflush(stdout);
		scanf("%f",&bet);
		// Check if bet is too less or too high
		if (bet > 499999999 ||  bet < 1)
		{
			printf("Hacker Alert!!\n");
			return 0;
		}
		number = rand() % 0x1337;
		printf("Guess number: ");
		fflush(stdout);
		scanf("%i",&guess);
		if(number == guess){
			money += bet;
			printf("Correct guess!\n");
		}else{
			money -= bet;
			printf("Wrong guess.. money left %.2f\n",money);
		}
	}

	// If money more than 1 billion will print the flag
	if (money < 1000000000){
		printf("See you next time..\n");
	}else{
		char flag[40];
		int fd = open("./flag.txt", O_RDONLY);
		read(fd, flag, 40);
		close(fd);
		printf("Congrats!! Flag is %s\n",flag);
	}
	return 0;
}