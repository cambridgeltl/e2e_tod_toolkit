// Welcome.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the Welcome component for introducing users to the
//              dialogue evaluation experiment.
//
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------


import React from 'react';
import './index.css';
import { Button, Result, Layout, Typography, Carousel, Descriptions } from 'antd';
import { ProfileOutlined } from '@ant-design/icons';
import {target_language, contact_name, contact_email} from "./configs";
import { useNavigate } from 'react-router-dom';

const { Paragraph, Text } = Typography;

const { Header, Content, Footer } = Layout;

const Welcome: React.FC = () => {
    const navigate = useNavigate();

    return(
    <Layout>
        <Header
            style={{
                backgroundColor:'#F5F5F5FF',
            }}
        >
        </Header>
        <Content className="site-layout">
            <Result
                icon={<ProfileOutlined />}
                title="Please Login or Register"
                extra={[
                    <Button key="login" onClick={ (e) => {
                        e.preventDefault()
                        console.log("Login!");
                        navigate('/login')
                    }
                    }>
                        Login
                    </Button>,

                    <Button type="primary" key="register" onClick={ (e) => {
                        e.preventDefault();
                        console.log("registration!");
                        navigate('/consent')
                    }
                    }>
                        Register
                    </Button>
                ]}
            >

                <div className="info">


                    <Paragraph>
                        <Text
                            strong
                            style={{
                                fontSize: 16,
                            }}
                        >
                            Welcome to our experimental study!
                            <br/>
                            <br/>
                            Here is a summary about this task.
                        </Text>
                    </Paragraph>

                    <Carousel autoplay autoplaySpeed={12000} effect="fade" dotPosition={"left"}>
                        <div>
                            <Descriptions bordered>
                                <Descriptions.Item span={2} label="Contact">{contact_name} {contact_email}</Descriptions.Item>
                                <Descriptions.Item span={1} label="Requirement">You are a native speaker of {target_language}.</Descriptions.Item>

                                <Descriptions.Item span={2} label="How much will I be paid">1 GBP per task</Descriptions.Item>
                                <Descriptions.Item span={1} label="How long will it take">5 minutes per task</Descriptions.Item>
                            </Descriptions>
                        </div>
                        <div>

                            <Descriptions bordered>
                                <Descriptions.Item span={3} label="Is my personal information required">Only your email is required for payment purposes.</Descriptions.Item>
                                <Descriptions.Item span={3} label="Can I do this task for multiple times">
                                    Yes, you can do this task for multiple times, and you will be paid for all your submission.
                                </Descriptions.Item>
                            </Descriptions>



                        </div>
                    </Carousel>

                    <br/>

                    <Paragraph>
                        <Text
                            strong
                            style={{
                                fontSize: 16,
                            }}
                        >

                            If you do not have an account, please click the Register button below to start.

                            1. You will find out what the experiment is about and what you will be asked to do.

                            2. You will also be asked to sign a consent form.

                            3. Then you will be headed to registration.
                            <br/>

                            <br/>

                            If you already have an account, please click the Login button above to start.

                        </Text>
                    </Paragraph>

                </div>


            </Result>

        </Content>
        <Footer style={{ textAlign: 'center', backgroundColor:'#F5F5F5FF' }}>Cambridge LTL ©2023</Footer>
    </Layout>
    )
}

export default Welcome;
