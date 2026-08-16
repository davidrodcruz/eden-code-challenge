@eden @webui
Feature: MPR Viewer - Eden PACS
  The viewer exposes clinical measurements through Cornerstone's mathematical
  annotation state instead of its rendered presentation layer.

  Background:
    Given the user navigates to the MPR viewer
    And the MPR viewer has finished loading

  @smoke @pacs
  Scenario: MPR viewer loads successfully
    Then take a screenshot of the page

  @measurement @pacs @smoke
  Scenario: Successful measurement creation registers exact coordinates
    Given the measurement tool is active
    When the user draws a line on viewport 0
    Then the measurement state should record accurate physical dimensions in mm
    And viewport 0 should have 1 active annotation

  @persist @pacs @measurement
  Scenario: Multiple measurements generate unique state identifiers
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the user draws a second line on viewport 0
    Then viewport 0 should have 2 active annotations
    And each measurement must have a unique state UID

  @zerodistance @pacs @measurement
  Scenario: Zero distance click does not create ghost annotations
    Given the measurement tool is active
    When the user double-clicks on viewport 0
    Then viewport 0 should have 0 annotations registered in the state

  @zoom @pacs @spatial
  Scenario: Measurement state persists accurately after zoom transformation
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the user activates the zoom tool from the circular menu
    And the user drags on viewport 0
    Then the exact measurement spatial data must persist without degradation

  @pan @pacs @spatial
  Scenario: Measurement world-coordinates remain fixed during panning
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the user activates the pan tool from the circular menu
    And the user drags on viewport 0
    Then the exact measurement spatial data must persist without degradation

  @scroll @pacs @spatial
  Scenario: Annotation state isolates correctly across Z-axis slices
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the viewport 0 measurement slice is captured
    And the user scrolls up on viewport 0
    Then the viewport slice should have changed
    And viewport 0 should have 0 visible annotations
    When the user scrolls down on viewport 0
    Then the viewport slice should return to the measurement slice
    And the exact measurement spatial data must persist without degradation

  @crossplane @pacs @axial
  Scenario: Axial measurement state is isolated from Coronal viewport
    Given the measurement tool is active
    When the user draws a line on viewport 0
    Then viewport 0 should have 1 active annotation
    And viewport 1 should have 0 annotations registered in the state

  @crossplane @pacs @sagittal
  Scenario: Sagittal measurement state is isolated from Axial viewport
    Given the measurement tool is active
    When the user draws a line on viewport 2
    Then viewport 2 should have 1 active annotation
    And viewport 0 should have 0 annotations registered in the state

  @edit @pacs @mutation
  Scenario: Dynamically modifying an existing measurement updates the state
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the user drags the endpoint of the existing measurement
    Then the measurement length state should dynamically update

  @delete @pacs @mutation
  Scenario: Deleting a measurement clears its UID from the state manager
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the user selects the measurement and presses Delete
    Then viewport 0 should have 0 annotations registered in the state

  @toolswitch @pacs @state
  Scenario: Switching to non-annotative tools locks measurement creation
    Given the pan tool is active
    When the user drags on viewport 0
    Then viewport 0 should have 0 annotations registered in the state

  @toolswitch @pacs @state @measurement
  Scenario: State integrity is maintained when toggling tools
    Given the measurement tool is active
    When the user draws a line on viewport 0
    And the user activates the pan tool from the circular menu
    And the user drags on viewport 0
    And the user activates the measurement tool from the circular menu
    And the user draws a second line on viewport 0
    Then viewport 0 should have 2 active annotations
    And each measurement must have a unique state UID

  @menu @pacs
  Scenario: Circular menu closes on outside click
    When the user opens the circular menu on viewport 0
    Then the circular menu should be visible
    When the user closes the circular menu by clicking outside
    Then the circular menu should not be visible
