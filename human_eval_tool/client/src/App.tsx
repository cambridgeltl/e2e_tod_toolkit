// App.tsx
// ----------------------------------------------------------------------------------------
// Description: This file contains the main App component and associated routing logic
//              for a React application. It includes conditional routing based on user
//              authentication status, using the useToken hook for token management.
// Author: Xiaobin Wang and Songbo Hu
// Date: 2023-12-16
// License: MIT License
// ----------------------------------------------------------------------------------------

import React, {useEffect} from 'react';
import './index.css';
import {useLocation, useRoutes,useNavigate} from 'react-router-dom'
import routes from "./router"
import {message} from "antd";
import useToken from './service/TokenService'

// Component to redirect to the assignment page
function ToAssignment(){
    const navigateTo = useNavigate()
    useEffect(() => {
        navigateTo("/assignment")
    }, []);
    return <div/>
}

// Component to redirect to the login page
function ToLogin(){
    const navigateTo = useNavigate()
    useEffect(() => {
        navigateTo("/")
        message.warning('You need to login first')
    }, []);
    return <div/>
}

// Component to handle authentication-based routing
function AuthRouter(){
    const { token, removeToken, setToken, getToken } = useToken();

    // Don't know why, but use token directly will fail.
    const isAuthenticated = getToken() !== null
    console.log("isAuthenticated")
    console.log(isAuthenticated)
    const location = useLocation()
    const routers = useRoutes(routes)

    // Redirects to the assignment page if authenticated and trying to access login
    if (isAuthenticated && location.pathname === '/login'){
        return <ToAssignment />
    }

    // Redirects to login if not authenticated and trying to access restricted pages
    if (!isAuthenticated && (location.pathname === '/assignment' || location.pathname === '/admin')){
        return <ToLogin />
    }

    // Returns the regular routing setup
    return routers
}


function App() {


    return (
        <div className='App'>
            <AuthRouter />
        </div>
    );
}

export default App;
