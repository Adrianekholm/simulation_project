import simpy
import random
import statistics
import matplotlib.pyplot as plt
import pandas as pd

results = {
    'num_staff': [],
    'avg_wait_time': [],
    'max_wait_time': [],
    'max_queue_length': [],
    'utilization': [],
    'avg_queue_length': [],
    'customers_reneged': [],
    'customers_served': [],
    'throughput_rate': []
}

SERVICE_TIME = 15.0
ARRIVAL_RATE = 0.2
SIM_TIME = 480
MAX_QUEUE_WAIT = 20

wait_times = []
max_wait_time = 0
max_queue_length = 0
total_busy_time = 0
queue_length_over_time = []
customers_reneged = 0
customers_served = 0

def reset_globals():
    global wait_times, max_wait_time, max_queue_length, total_busy_time, queue_length_over_time, customers_reneged, customers_served
    wait_times = []
    max_wait_time = 0
    max_queue_length = 0
    total_busy_time = 0
    queue_length_over_time = [(0, 0)]
    customers_reneged = 0
    customers_served = 0

class Company:
    def __init__(self, env, num_staff):
        self.env = env
        self.staff = simpy.Resource(env, num_staff)

    def help_customer(self, customer):
        global total_busy_time
        service_time = random.randint(5, int(SERVICE_TIME))
        yield self.env.timeout(service_time) #Time to help customer
        total_busy_time += service_time

def customer_calling(env, customer, company):
    global max_wait_time, customers_reneged, customers_served
    arrival_time = env.now
    print(f'Customer {customer} called in at {arrival_time:.2f}')

    with company.staff.request() as request:
        queue_length = len(company.staff.queue)
        update_max_queue_length(queue_length)
        record_queue_length(env.now, queue_length)

        patience = random.randint(15, MAX_QUEUE_WAIT)  #Max time customer will wait in queue
        result = yield request | env.timeout(patience)

        if request in result:
            #Customer got the resource before timeout
            wait = env.now - arrival_time
            wait_times.append(wait)
            if wait > max_wait_time:
                max_wait_time = wait

            print(f'Customer {customer} connected to support at {env.now:.2f} after waiting {wait:.2f} minutes.')
            yield env.process(company.help_customer(customer))
            print(f'Customer {customer} finished call at {env.now:.2f}')
            customers_served += 1
        else:
            #Customer left the queue due to impatience
            print(f'Customer {customer} left the queue at {env.now:.2f} after waiting {patience:.2f} minutes.')
            customers_reneged += 1

        #Record queue length after the customer leaves or gets service
        queue_length = len(company.staff.queue)
        record_queue_length(env.now, queue_length)

def run_customer_service(env, num_staff):
    company = Company(env, num_staff)

    #Creating 3 customers from start
    for customer in range(3):
        env.process(customer_calling(env, customer, company))

    while True:
        yield env.timeout(random.expovariate(ARRIVAL_RATE))
        customer += 1
        env.process(customer_calling(env, customer, company))

def get_average_wait_time(wait_times):
    if wait_times:
        average_wait = statistics.mean(wait_times)
    else:
        average_wait = 0
    return average_wait

def update_max_queue_length(current_queue_length):
    global max_queue_length
    if current_queue_length > max_queue_length:
        max_queue_length = current_queue_length

def calculate_utilization(total_busy_time, num_staff, sim_time):
    return (total_busy_time / (num_staff * sim_time)) * 100 #In percentage

def record_queue_length(time, queue_length):
    queue_length_over_time.append((time, queue_length))

def calculate_average_queue_length(queue_length_over_time, sim_time):
    if not queue_length_over_time:
        return 0

    #Sort the list by time
    queue_length_over_time.sort(key=lambda x: x[0])

    total_area = 0
    last_time = 0
    last_queue_length = 0

    for time, queue_length in queue_length_over_time:
        duration = time - last_time
        total_area += last_queue_length * duration
        last_time = time
        last_queue_length = queue_length

    #Add the last interval till the end of simulation
    duration = sim_time - last_time
    total_area += last_queue_length * duration

    average_queue_length = total_area / sim_time
    return average_queue_length

def run_simulation(num_staff):
    #Run simulation and save results
    reset_globals()
    env = simpy.Environment()
    env.process(run_customer_service(env, num_staff))
    env.run(until=SIM_TIME)

    avg_wait = get_average_wait_time(wait_times)
    utilization = calculate_utilization(total_busy_time, num_staff, SIM_TIME)
    avg_queue_length = calculate_average_queue_length(queue_length_over_time, SIM_TIME)

    #Calculate throughput rate
    throughput_rate = customers_served / SIM_TIME

    #Save results
    results['num_staff'].append(num_staff)
    results['avg_wait_time'].append(avg_wait)
    results['max_wait_time'].append(max_wait_time)
    results['max_queue_length'].append(max_queue_length)
    results['utilization'].append(utilization)
    results['avg_queue_length'].append(avg_queue_length)
    results['customers_reneged'].append(customers_reneged)
    results['customers_served'].append(customers_served)
    results['throughput_rate'].append(throughput_rate)  # Lägg till denna rad

    #Print results for each simulation
    print(f'-- Results for {num_staff} staff --')
    print(f'Customers served: {customers_served}')
    print(f'Customers who left the queue: {customers_reneged}')
    print(f'Throughput rate: {throughput_rate:.2f} customers per minute.')
    print(f'Average wait time: {avg_wait:.2f} minutes.')
    print(f'Maximum wait time: {max_wait_time:.2f} minutes.')
    print(f'Maximum queue length: {max_queue_length}')
    print(f'Average queue length: {avg_queue_length:.2f}')
    print(f'Utilization: {utilization:.2f}%.')
    print('------------------------------\n')

def main():
    #Setup
    random.seed(42)
    #List of different numbers of staff to test with
    staff_list = [1, 2, 3, 4, 5]

    for num_staff in staff_list:
        run_simulation(num_staff)

    df = pd.DataFrame(results)

    #Average waiting time (minutes)
    plt.figure(figsize=(10, 6))
    plt.bar(df['num_staff'], df['avg_wait_time'], color='skyblue')
    plt.xlabel('Number of Staff')
    plt.ylabel('Average waiting time (minutes)')
    plt.title('Average waiting time vs Number of Staff')
    plt.xticks(df['num_staff'])#Säkerställ att alla antal visas på x-axeln
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
    
    #Average queue length
    plt.figure(figsize=(10, 6))
    plt.bar(df['num_staff'], df['avg_queue_length'], color='purple')
    plt.xlabel('Number of Staff')
    plt.ylabel('Average Queue Length')
    plt.title('Average Queue Length vs Number of Staff')
    plt.xticks(df['num_staff'])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
    
    #Utilization
    plt.figure(figsize=(10, 6))
    plt.bar(df['num_staff'], df['utilization'], color='gold')
    plt.xlabel('Number of Staff')
    plt.ylabel('Utilization (%)')
    plt.title('Utilization vs Number of Staff')
    plt.xticks(df['num_staff'])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
    
    #Customers leaving queue
    plt.figure(figsize=(10, 6))
    plt.bar(df['num_staff'], df['customers_reneged'], color='red')
    plt.xlabel('Number of Staff')
    plt.ylabel('Number of Customers Who Left Queue')
    plt.title('Number of Customers Who Left Queue vs Number of Staff')
    plt.xticks(df['num_staff'])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    #Throughput: Customers served per minute
    plt.figure(figsize=(10, 6))
    plt.bar(df['num_staff'], df['throughput_rate'], color='blue')
    plt.xlabel('Number of Staff')
    plt.ylabel('Throughput Rate (customers per minute)')
    plt.title('Throughput Rate vs Number of Staff')
    plt.xticks(df['num_staff'])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
