// Login.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the Login component for handling user authentication
//              in a dialogue evaluation experiment. It includes a form for email and
//              password input and navigation logic based on authentication status.
//
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import React, {useEffect} from "react";
import {message, Input, Button, Collapse, Form, Row, Col, Layout} from 'antd';
import {contact_address, serverUrl} from "./configs";
import {contact_name, contact_email} from "./configs";
import {NavigateFunction, useNavigate} from "react-router-dom";
import useToken from "./service/TokenService";

const {Header, Content, Footer} = Layout;

// Type definition for form fields
type LoginFieldType = {
    email: string;
    password: string;
};

// Function to handle form submission failure
function onFinishFailed(errorInfo:any){
    console.log('Failed:', errorInfo);
    message.error('Failed to log in.');
}

const Login: React.FC = () => {
    const navigate = useNavigate();
    const { token, removeToken, setToken, getUserRole } = useToken();

    // Function to handle form submission on login
    function onFinish(values: LoginFieldType){

        console.log('Received values of form: ', values);
        fetch(serverUrl+'/api/login', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "email" : values.email, "password" : values.password})
        })
            .then(function (response) {
                console.log("response");
                console.log(response);
                return response.json();
            })
            .then(function (json) {

                if (json.success === false)
                {
                    message.error(json.msg);
                }
                else
                {
                    setToken(json.access_token);
                }
            });
    }

    // Effect to navigate to a different route based on authentication status
    useEffect(() => {
        if (token) {

            navigate('/assignment');
        }
    }, [token, navigate]); // Dependency array with token

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
                        <Collapse defaultActiveKey={['1','2','3']}>
                            <Collapse.Panel header="Contact" key="1" >
                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}>
                                    {contact_name}
                                    <br/>
                                    {contact_address}
                                    <br/>
                                    {contact_email}
                                </p>
                            </Collapse.Panel>
                            <Collapse.Panel header="Login" key="3">

                                <br/>
                                In order to start your task, please log in with your account. If you do not have an account yet, please click this { }
                                <Button size={"small"} key="register" onClick={ (e) => {
                                    e.preventDefault();
                                    navigate('/consent');
                                }
                                }>
                                    Register
                                </Button> { } button.

                                <br/>
                                <br/>
                                <br/>
                                <br/>

                                            <Form
                                                name="login"
                                                labelCol={{ span: 8 }}
                                                wrapperCol={{ span: 16 }}
                                                style={{ maxWidth: 600 }}
                                                initialValues={{ remember: true }}
                                                onFinish={(x) => onFinish(x)}
                                                onFinishFailed={onFinishFailed}
                                                autoComplete="off"
                                            >

                                                <Form.Item<LoginFieldType>
                                                    label="Email"
                                                    name="email"
                                                    rules={[{ required: true, message: 'Please input your email!' }, {type: 'email', message: 'Please enter a valid email!'}]}
                                                    >
                                                    <Input />
                                                </Form.Item>

                                                <Form.Item<LoginFieldType>
                                                    label="Password"
                                                    name="password"
                                                    rules={[{ required: true, message: 'Please input your password!' },  { type: 'string', min: 6,  message: 'Password should be longer than 6 characters.' }]}
                                                    >
                                                    <Input.Password />
                                                </Form.Item>

                                    <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                        <Button type="primary" htmlType="submit">
                                            Submit
                                        </Button>
                                    </Form.Item>
                                </Form>

                            </Collapse.Panel>
                        </Collapse>
                    </div>
                </Content>
                <Footer style={{ textAlign: 'center', backgroundColor:'#F5F5F5FF' }}>Cambridge LTL ©2023</Footer>
            </Layout>
        )
}


export default Login;
