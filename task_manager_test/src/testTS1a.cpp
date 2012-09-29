
#include "task_manager_lib/TaskScheduler.h"
#include "task_manager_lib/DynamicTask.h"
#include "task_manager_test/TaskIdle.h"

void wait5sec()
{
	printf("Waiting:"); fflush(stdout);
	for (unsigned int i=0;i<5;i++) {
		sleep(1);
		printf(".");
		fflush(stdout);
	}
	printf("\n");
}

void testTSa()
{
    ros::NodeHandle nh("~");
	TaskEnvironment env;
	printf("\n*******************\n\nTesting basic task scheduler functions (A)\n");
	printf("Creating tasks\n");
	TaskDefinition *idle = new TaskIdle(&env);
	TaskDefinition *dtask = new DynamicTask("./lib/libTaskTest.so",&env);
	printf("Creating task scheduler\n");
	TaskScheduler ts(nh,idle, 1.0);
	ts.printTaskDirectory();
	printf("Adding tasks\n");
	ts.addTask(dtask);
	printf("Configuring tasks\n");
	ts.configureTasks();
	// don't delete tasks, because the ts took responsibility for them
	ts.printTaskDirectory();
	printf("Launching idle task\n");
	ts.startScheduler();
	wait5sec();
	printf("Destroying task scheduler\n");
}



int main(int argc, char * argv[])
{
    ros::init(argc,argv,"client");

	testTSa();

	return 0;
}
