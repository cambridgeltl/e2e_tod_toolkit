// AssignmentResult.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the AssignmentResult component for displaying the
//              result of the dialogue evaluation task. It uses a button to allow users
//              to perform another task.
// Author: Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------


import React from 'react';
import './index.css';
import { Button, Result, Layout} from 'antd';
import { useNavigate } from 'react-router-dom';

const { Header, Content, Footer } = Layout;

const AssignmentResult: React.FC = () => {
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

                status={"success"}
                title="Your submission was received!"
                subTitle="Thanks again for your contribution to our experiential study. You may do a similar task by clicking one more task button or closing this web page."
                extra={[
                    <Button type="primary" key="again" onClick={ (e) => {
                        e.preventDefault()
                        navigate('/assignment')
                    }
                    }>
                        One more task
                    </Button>
                ]}
            >
            </Result>

        </Content>
        <Footer style={{ textAlign: 'center', backgroundColor:'#F5F5F5FF' }}>Cambridge LTL ©2023</Footer>
    </Layout>
    )
}

export default AssignmentResult;