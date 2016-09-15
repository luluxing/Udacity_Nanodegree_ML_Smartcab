import random, numpy, math
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""   
    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.valid_actions = [None, 'forward', 'left', 'right']
        self.matrix = {}
        self.success = []
        self.alpha = 1
        self.gamma = 0.6
        self.epsilon = 1
        #self.breaktraffic = []
        #self.deadline = 0
        #self.timepercentage = []
        #self.loop = []
        
    def reset(self, destination=None): 
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required
        #self.deadline = self.env.get_deadline(self)
        self.success += [0]
        #self.breaktraffic += [0]
        # print self.loop
        # self.loop = []
        
    
    def get_decay_rate(self, t):
        #Decay rate for alpha and epsilon
        #time step: first movement (1), second movement (2), etc.
        if t == 0:
            return 1
        return 1 / float(t)
        #return 1.0 / math.exp(t)
        #return 1.0 / math.sqrt(t)
        #return 1.


    def get_max_utility_action(self, qtable, s):
        tmp = [qtable[(s, x)] for x in self.valid_actions]
        maxQ = max(tmp)
        count = tmp.count(maxQ)
        if count > 1:
            best = [i for i in range(len(self.valid_actions)) if tmp[i] == maxQ]
            i = random.choice(best)
        else:
            i = tmp.index(maxQ)
        return self.valid_actions[i]

    def get_state(self):
        self.next_waypoint = self.planner.next_waypoint()
        inputs = self.env.sense(self)
        return (self.next_waypoint, inputs['light'], inputs['oncoming'], inputs['left'], inputs['right'])

    def break_traffic(self, s, a):
        if a == 'forward':
            if s[1] == 'red':
                return True
        elif a == 'left':
            if not (s[1] == 'green' and (s[2] == None or s[2] == 'left')):
                return True
        elif a == 'right':
            if not (s[1] == 'green' or s[3] != 'forward'):
                return True
        return False


    def update(self, t):   
        self.alpha *= self.get_decay_rate(t)
        self.epsilon *= self.get_decay_rate(t) 
        # TODO: Update state
        self.current_state = self.get_state()

        #self.loop += [self.env.agent_states[self]['location']]
                
        # initialize the Qtable
        for a in self.valid_actions:
            if (self.current_state, a) not in self.matrix:             
                self.matrix[(self.current_state,a)] = 0.

        # explore or exploitation
        if random.random() < self.epsilon:    # explore       
            action = random.choice(self.valid_actions)
        else: # exploitation
            action = self.get_max_utility_action(self.matrix, self.current_state)
        
        # check whether the agent has broken traffic rules
        # if self.break_traffic(self.current_state, action):
        #     self.breaktraffic[-1] += 1

        # Execute action and get reward
        reward = self.env.act(self, action)
        # new state after taking action
        self.next_state = self.get_state()
        
        # Reach destination!
        if self.env.agent_states[self]['location'] == self.env.agent_states[self]['destination']:
            #self.timepercentage.append(1. * t/self.deadline)
            self.success[-1] = 1
            
        else:      
            for a in self.valid_actions:
                if (self.next_state, a) not in self.matrix:             
                    self.matrix[(self.next_state,a)] = 0.
            nextaction = self.get_max_utility_action(self.matrix, self.next_state)
            change = self.alpha * (reward + self.gamma * self.matrix[(self.next_state, nextaction)])
            self.matrix[(self.current_state, action)] = self.matrix[(self.current_state, action)] * (1 - self.alpha) + change
          
            

def run():
    """Run the agent for a finite number of trials."""
    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    result = []
    for x in xrange(1):
        # Now simulate it
        sim = Simulator(e, update_delay=0.005, display=False)  # create simulator (uses pygame when display=True, if available)
        # NOTE: To speed up simulation, reduce update_delay and/or set display=False
        sim.run(n_trials=100)  # run for a specified number of trials
        # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line
        ratio = numpy.mean(a.success[100*x:100*(x+1)+1])
        result.append(ratio)

       
    print result



if __name__ == '__main__':
    run()
    