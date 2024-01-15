// ConsentForm.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the ConsentForm component for displaying a consent form
//              to participants in a dialogue evaluation experiment. It includes the
//              participant consent information and a checkbox for agreement.
//
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------


import React, {useState} from "react";
import {Button, Collapse, Form, Layout, Checkbox} from 'antd';
import {contact_name, contact_email, contact_address} from "./configs";
import {NavigateFunction, useNavigate} from "react-router-dom";
const {Header, Content, Footer} = Layout;

type ConsentFieldType = {
    consent: boolean;
};

const ConsentForm: React.FC = () => {
    const navigate = useNavigate();
    const [clicked, setClicked] = useState<boolean>(false);

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
                            <Collapse.Panel header="consent" key="3">
                                <p style={{"fontSize": 15, 'whiteSpace': 'pre-line'}}><b>

                                    <b>Participant Consent Form</b>
                                    <br/>
                                    <br/>
                                    Project title: Advancing Cross-lingual Transfer for Conversational AI
                                    <br/>
                                    <br/>
                                    Research team: Prof. Anna Korhonen, Dr. Ivan Vulić, Songbo Hu
                                    <br/>
                                    <br/>
                                    If you have any questions, please contact Songbo Hu, sh2091@cam.ac.uk
                                    <br/>
                                    <br/>
                                    1. I confirm that I have read and understand the information sheet dated 11/01/2022 for the above mentioned study and have had the opportunity to ask questions.
                                    <br/>
                                    <br/>
                                    2. I understand that my participation is voluntary and that I am free to withdraw at any time, without giving any reason, and without my rights being affected.
                                    <br/>
                                    <br/>
                                    3. I understand that any data that are collected will be used and stored anonymously, in accordance with the Data Protection Act. Results are normally presented in terms of groups of individuals. If any individual data were presented, the data would be completely anonymous, without any means of identifying the individuals involved.
                                    <br/>
                                    <br/>
                                    4. I understand that these data may be used in analyses, publications, and conference presentations by researchers at the University of Cambridge and their collaborators at other research institutions. I give permission for these individuals to have access to these data.
                                    <br/>
                                    <br/>
                                    5. I understand that personal information (such as language background, age, gender, and other important information such as residence, place of birth, etc.) will be collected as part of this research. Full data will only be accessible to the research team. However, anonymised data may be used in analyses, publications and conference presentations.  Anonymised data will be deposited to the Apollo---University of Cambridge Repository,  https://www.repository.cam.ac.uk/, for future research and study. For full details on how we use your personal information, see https://www.information-compliance.admin.cam.ac.uk/data-protection/research-participant-data
                                    <br/>
                                    <br/>
                                    6. I agree to participate in the above mentioned study run by Songbo Hu, a PhD student member at the Faculty of MML at the University of Cambridge.
                                </b></p>

                                <Form
                                    name="consent"
                                    initialValues={{ remember: true }}
                                    onFinish={(x) => navigate("/register")}
                                    autoComplete="off"
                                >

                                    <Form.Item<ConsentFieldType>
                                        label="I agree with the above Participant Consent Form."
                                        name="consent"
                                    >
                                        <Checkbox onClick={() => {setClicked(!clicked)}}/>
                                    </Form.Item>
                                    <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                        <Button disabled={!clicked}  type="primary" htmlType="submit">
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


export default ConsentForm;
