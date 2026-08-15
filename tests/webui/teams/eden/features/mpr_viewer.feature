@eden @webui
Feature: MPR Viewer - Eden PACS

  @smoke @pacs
  Scenario: MPR viewer loads successfully
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    Then take a screenshot of the page

  @measurement @pacs
  Scenario: Complete ruler measurement from circular menu
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user draws a line on viewport 0
    Then viewport 0 should have 1 annotation
    And the measurement unit should be "mm"
    And the measurement value should be a positive number
    And take a screenshot of the page

  @toolswitch @pacs
  Scenario: Explicit deactivation after measurement
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user draws a line on viewport 0
    And the user activates the pan tool from the circular menu
    And the user drags on viewport 0
    Then viewport 0 should have 1 annotation
    And take a screenshot of the page

  @zoom @pacs
  Scenario: Annotation persists after zoom
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user draws a line on viewport 0
    And the user activates the zoom tool from the circular menu
    And the user drags on viewport 0
    Then viewport 0 should have 1 annotation
    And take a screenshot of the page

  @persist @pacs
  Scenario: Active state persists for consecutive measurements
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user draws a line on viewport 0
    And the user draws a second line on viewport 0
    Then viewport 0 should have 2 annotations
    And take a screenshot of the page

  @menu @pacs
  Scenario: Circular menu closes on outside click
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user opens the circular menu on viewport 0
    Then the circular menu should be visible
    When the user closes the circular menu by clicking outside
    Then the circular menu should not be visible
    And take a screenshot of the page

  @zerodistance @pacs
  Scenario: Zero distance click does not create annotation
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user double-clicks on viewport 0
    Then viewport 0 should have 0 annotations
    And take a screenshot of the page

  @crossplane @pacs
  Scenario: Measurement is independent between viewports
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user draws a line on viewport 1
    Then viewport 1 should have 1 annotation
    And viewport 0 should have 0 annotations
    And take a screenshot of the page
    And the browser is closed and the video is saved

  @scroll @pacs
  Scenario: Annotation model persists across slice navigation
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading
    When the user activates the measurement tool
    And the user draws a line on viewport 0
    Then viewport 0 should have 1 annotation
    When the user scrolls up on viewport 0
    Then viewport 0 should have 1 annotation
    When the user scrolls down on viewport 0
    Then viewport 0 should have 1 annotation
    And take a screenshot of the page
