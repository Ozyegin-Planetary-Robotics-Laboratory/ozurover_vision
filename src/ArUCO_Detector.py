#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2 as cv
import numpy as np
from ozurover_messages.msg import ArUco
class Node:
    def __init__(self):
        rospy.init_node("ares/aruco/detecter")
        self.pub = rospy.Publisher("ares/goal/aruco",ArUco,1)
        self.sub = rospy.Subscriber("rgb/image_rect_color",Image,self.callback)
        self.MARKER_SIZE = 20.0
        self.LEFT_CAM_HD = {
                            'fx': 533.895,
                            'fy': 534.42,
                            'cx': 642.65,
                            'cy': 349.4705,
                            'k1': -0.0557809,
                            'k2': 0.0279374,
                            'p1': 0.000647675,
                            'p2': -0.000394777,
                            'k3': -0.0106177
                            }
        self.CAM_MAT = np.array([[self.LEFT_CAM_HD['fx'], 0, self.LEFT_CAM_HD['cx']],
                    [0, self.LEFT_CAM_HD['fy'], self.LEFT_CAM_HD['cy']],
                               [0, 0, 1]])
        self.DIST_COEF = np.array([-0.0557809, 0.0279374, 0.000647675, -0.000394777, -0.0106177])
        self.MARKER_DICT = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_50)
        self.PARAM_MARKERS = cv.aruco.DetectorParameters_create()
    

    def detect_markers(self,frame):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        self.marker_corners, self.marker_IDs, reject = cv.aruco.detectMarkers(gray, self.MARKER_DICT, parameters=self.PARAM_MARKERS)
        return self.marker_corners, self.marker_IDs
    

    def estimate_pose(self,marker_corners):
        self.rVec, self.tVec, _ = cv.aruco.estimatePoseSingleMarkers(marker_corners, self.MARKER_SIZE, self.CAM_MAT, self.DIST_COEF)
        return self.tVec


    def aruco_func(self,frame):
        marker_corners, marker_IDs = self.detect_markers(frame)

        if marker_corners:
            tVec = self.estimate_pose(marker_corners)

            total_markers = range(0, marker_IDs.size)
            for ids, i in zip(marker_IDs, total_markers):
                aruco_tag = ArUco()
                aruco_tag.Pose.position.x = tVec[i][0][0]
                aruco_tag.Pose.position.y = tVec[i][0][1]
                aruco_tag.Pose.position.z = tVec[i][0][2]
                aruco_tag.header.frame_id = "zed2i_left_camera_frame"
                

                self.pub.publish(aruco_tag)


    def callback(self, image_data):
        try:
            # Convert ROS Image message to OpenCV image
            bridge = CvBridge()
            cv_image = bridge.imgmsg_to_cv2(image_data, desired_encoding="bgr8")
            self.aruco_func(cv_image)
        except Exception as e:
            rospy.logerr(f"Error processing image: {repr(e)}")



if __name__ == "__main__":
    node = Node()
    rospy.spin()