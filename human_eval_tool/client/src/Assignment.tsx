// Assignment.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the Assignment component for a dialogue evaluation
//              experiment in a React application. It includes functionalities for
//              chatting, evaluating the dialogue system, and fetching tasks based on
//              user authorization.
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import React from "react";
import {message, Input, Button, Collapse, Form, Tour, Layout, Rate, Timeline, Radio, Select} from 'antd';
import {serverUrl, dial_eval_options} from "./configs";
import {target_language, contact_name, contact_email, contact_address} from "./configs";
import {NavigateFunction, useNavigate} from "react-router-dom";
import Chatbox from "./Chatbox";
import { useEffect, useState, createContext, useRef} from "react";
import parse from "html-react-parser";
import type { TourProps } from 'antd';
import useToken from "./service/TokenService";

const {Header, Content, Footer} = Layout;

// Type definitions for various data structures used in the component
type EvaluateFieldType = {
    overall: number;
    property: string[];
    goal : number;
    feedback : string;
};

type dialogueEvalType = {score: number, issue: string[], correct: string}

type dialogueUttType = { utterance: string, speaker: "system" | "user", evaluation: dialogueEvalType | null};

// Context for managing dialogue history
export const DialogueHistoryContext = createContext<{dialogueHistory: dialogueUttType[]; setDialogueHistory: React.Dispatch<React.SetStateAction<dialogueUttType[]>>} | null>(null);

// Function to handle form submission on evaluation completion
function onFinish(values: EvaluateFieldType, dialogueHistory: dialogueUttType[],  navigate: NavigateFunction, token: string | null){

    console.log("submit")
    console.log('Received values of form: ', values);
    console.log('Retried dialogue history: ', dialogueHistory);
    console.log("body")
    console.log({ "overall" : values.overall, "goal" : values.goal, "property" : values.property, "feedback" : values.feedback, "history" : dialogueHistory})

    fetch(serverUrl+'/api/save_result', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({ "overall" : values.overall, "goal" : values.goal, "property" : values.property, "feedback" : values.feedback, "history" : dialogueHistory})
    })
        .then(function (response) {
            console.log(response);
            return response.json();
        })
        .then(function (json) {

            console.log(json)

          if(json.success === false){
                message.error(json.msg);
          }
          else
          {
                navigate('/result');
          }
        });
}

// Function to handle form submission failure
function onFinishFailed(errorInfo:any){
    console.log('Failed:', errorInfo);
    message.error('Please complete the following evaluation questions!');
}

// Function to fetch the task for the user
function getTask(setUserGoal: React.Dispatch<React.SetStateAction<string[]>>, token: string | null) {
    if (!token) {
        console.error("No token available for authorization");
        return;
    }


    fetch(serverUrl+'/api/get_task', { // Update with your server URL
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.task) {

                console.log(data.task)
                setUserGoal(data.task.task); // Assuming the task is an array of strings
            } else {
                console.error('Failed to fetch task data:', data.msg);
            }
        })
        .catch(error => {
            console.error('Error fetching task data:', error);
        });
}



const Assignment: React.FC = () => {
    const navigate = useNavigate();
    const [dialogueHistory, setDialogueHistory] = useState<dialogueUttType[]>([]);
    const [userGoal, setUserGoal] = useState<string[]>([]);
    const [openTour, setOpenTour] = useState<boolean>(true);
    const ref0 = useRef(null);
    const ref1 = useRef(null);
    const ref2 = useRef(null);
    const ref3 = useRef(null);
    const { token, removeToken, setToken, getUserRole, getUserPermissions } = useToken();

    const [hasAccessControl, setHasAccessControl] = useState<boolean>(false);

    // Function to fetch access control status
    const fetchAccessControlStatus = () => {
        if (!token) {
            console.error("No token available for authorization");
            return;
        }

        console.log("fetchAccessControlStatus")

        fetch(serverUrl+'/api/get_access_control', {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            }
        })
            .then(response => {
                console.log("response")
                console.log(response)
                console.log("!response.ok")
                console.log(!response.ok)
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {

                console.log("data")
                console.log(data)

                if (data.success) {
                    console.log("setHasAccessControl data")
                    console.log(data)
                    setHasAccessControl(data.access_control_enabled);
                } else {
                    console.error('Failed to fetch access control status:', data.msg);
                }
            })
            .catch(error => {
                console.error('Error fetching access control status:', error);
            });
    };

    // Fetch access control status and handle user permissions for conditional rendering
    useEffect(() => {
        fetchAccessControlStatus();
    }, [token]);

    useEffect(() => {
        const userPermissions = getUserPermissions();
        console.log("userPermissions")
        console.log(userPermissions)

        if(hasAccessControl){
            if (!userPermissions.includes("visit_task_page_with_access_control")) {
                message.warning('Access Denied. Redirecting to the home page. For questions, please contact the task organiser.');
                navigate('/'); // Redirect to the root page
            }
        }else{
            if (!userPermissions.includes("visit_task_page")) {
                message.warning('Access Denied. Redirecting to the home page. For questions, please contact the task organiser.');
                navigate('/'); // Redirect to the root page
            }
        }

    }, [hasAccessControl, getUserPermissions, navigate]);


    const steps: TourProps['steps'] = [
        {
            title: 'Welcome.',
            description: 'Welcome to our experimental study. Please email me if you have any questions.',
            target: () => ref0.current,
        },
        {
            title: 'Follow the instruction.',
            description: 'Please carefully read the instruction.',
            target: () => ref1.current,
        },
        {
            title: 'Chat with the system.',
            description: 'You should chat with the system to achieve the above goals. Please note that you can click each system response to give feedback.',
            target: () => ref2.current,
        },
        {
            title: 'Evaluate the system.',
            description: 'Please answer these questions to evaluate the performance of this system.',
            target: () => ref3.current,
        },
    ];

    useEffect(() => {
        console.log("Assignment dialogueHistory")
        console.log(dialogueHistory)
    }, [dialogueHistory]);

    useEffect(() =>{
        getTask(setUserGoal, token)
    }, [])

    return(

            <Layout>
                <Header
                    style={{
                        backgroundColor:'#F5F5F5FF',
                        padding: 0,
                    }}
                >
                    <div style={{display: 'flex', justifyContent: 'center',    alignItems: 'center'}}>
                        <b>
                            Dialogue Evaluation Experiment
                        </b>
                    </div>

                </Header>

                <Content className="site-layout">
                    <div>
                        <Collapse defaultActiveKey={['1','2','3','4']}>
                            <Collapse.Panel ref={ref0} header="Contact" key="1" >
                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}>
                                    {contact_name}
                                    <br/>
                                    {contact_address}
                                    <br/>
                                    {contact_email}
                                </p>
                            </Collapse.Panel>


                            <Collapse.Panel ref={ref1} header="Instruction" key="2" >

                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}>
                                    Imagine having a conversation with a telephone (or online) assistant where you want to complete the following specific task:
                                </p>

                                <br/>
                                <br/>

                                <Timeline>
                                    {
                                    userGoal.map((goal, index) => (
                                            <Timeline.Item key = {index}>
                                                {parse(goal)}.
                                            </Timeline.Item>
                                        ))
                                    }

                                </Timeline>

                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}>
                                    In this experimental study, we ask you to <b>be the user</b>. Try and imagine an actual conversation you might have with an employee of a hotel or an airline, or at a tourist information office – the aim is to engage a <b>natural conversation</b> that could take place between an {target_language} native speaker and the assistant.
                                </p>

                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}>
                                    Please remember to answer the questions at the end of this webpage to provide your evaluation of the system. You may also <b>click each system response</b> to provide feedback to each individual system response.

                                </p>


                            </Collapse.Panel>



                            <Collapse.Panel  ref={ref2} header="Chat" key="3">
                                {/*https://stackoverflow.com/questions/64407387/passing-data-from-child-to-parent-component-react-hooks*/}
                                <DialogueHistoryContext.Provider value={{dialogueHistory, setDialogueHistory}}>
                                    <Chatbox/>
                                </DialogueHistoryContext.Provider>

                            </Collapse.Panel>

                            <Collapse.Panel  ref={ref3} header="Evaluate" key="4">

                                <Form

                                    name="evaluation"
                                    onFinish={(x) => onFinish(x,  dialogueHistory, navigate,token)}
                                    onFinishFailed={onFinishFailed}
                                    autoComplete="off"
                                    initialValues={{
                                        ["feedback"]: "",
                                    }}
                                >

                                    <Form.Item<EvaluateFieldType>
                                        label="What is your overall satisfaction of the system."
                                        name="overall"
                                        rules={[{ required: true, message: 'Please rate the system!' }]}
                                    >
                                        <Rate />
                                    </Form.Item>

                                    <Form.Item<EvaluateFieldType>
                                        label="Does the system help you to achieve your goal?"
                                        name="goal"
                                        rules={[{ required: true, message: 'Please tell us if the system helps you to achieve your goal!' }]}
                                    >
                                        <Radio.Group>
                                            <Radio value={1}>Yes</Radio>
                                            <Radio value={2}>Partially</Radio>
                                            <Radio value={3}>No</Radio>
                                        </Radio.Group>

                                    </Form.Item>


                                    <Form.Item<EvaluateFieldType>
                                        label="Which of the following properties does this system achieve?"
                                        name="property"
                                        rules={[{ required: true, message: 'Please tell us if the system achieves any of the following properties!' }]}

                                    >

                                        <Select
                                            mode="multiple"
                                            allowClear
                                            style={{ width: '100%' }}
                                            placeholder="Please select"
                                            options={dial_eval_options}
                                        />
                                    </Form.Item>

                                    <Form.Item<EvaluateFieldType>
                                        label="Do you have any feedback about the system?"
                                        name="feedback"
                                    >

                                        <Input/>
                                    </Form.Item>


                                    <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                        <Button type="primary" htmlType="submit">
                                            Submit
                                        </Button>
                                    </Form.Item>
                                </Form>
                            </Collapse.Panel>
                        </Collapse>
                        <Tour open={openTour}
                              onClose={() => {
                                  setOpenTour(false)
                                  window.scrollTo(0, 0);
                              }}
                              steps={steps}
                        />

                    </div>

                </Content>
                <Footer style={{ textAlign: 'center', backgroundColor:'#F5F5F5FF' }}>Cambridge LTL ©2023</Footer>
            </Layout>
        )
}


export default Assignment;
